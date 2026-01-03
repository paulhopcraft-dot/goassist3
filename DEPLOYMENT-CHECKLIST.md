# GoAssist v3.0 - Production Deployment Checklist

## Pre-Deployment

### 1. Environment Configuration ✓

- [ ] Copy `.env.example` to `.env`
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `MAX_CONCURRENT_SESSIONS=100`
- [ ] Configure LLM credentials (`LLM_API_KEY`)
- [ ] Set production LLM endpoint (`LLM_BASE_URL`)
- [ ] Choose LLM model (`LLM_MODEL_NAME`)
- [ ] Configure ASR model path (`ASR_MODEL_PATH`)
- [ ] Choose TTS engine (`TTS_ENGINE=coqui` or `bark`)
- [ ] Enable CSRF protection (`CSRF_ENABLED=true`)
- [ ] Set secure session secret

### 2. Model Setup ✓

**ASR (Whisper):**
- [ ] Download Whisper model (recommended: large-v3)
- [ ] Place in accessible path
- [ ] Set `ASR_MODEL_PATH=/path/to/whisper`
- [ ] Test: Model loads without errors

**TTS:**
- [ ] Choose engine: Coqui TTS or Bark
- [ ] Install engine dependencies
- [ ] Test: TTS generates audio
- [ ] Verify: Audio quality acceptable

**LLM:**
- [ ] API key configured
- [ ] Endpoint reachable
- [ ] Rate limits understood
- [ ] Billing alerts set up

### 3. Avatar (Optional) ✓

- [ ] NVIDIA Audio2Face installed
- [ ] gRPC endpoint accessible
- [ ] Set `ENABLE_AVATAR=true`
- [ ] Set `AUDIO2FACE_GRPC_URL=host:port`
- [ ] Test: Blendshapes generate

### 4. Infrastructure ✓

**Resources:**
- [ ] CPU: 4+ cores (8+ recommended)
- [ ] RAM: 8GB+ (16GB+ recommended)
- [ ] Storage: 50GB+ (for models)
- [ ] Network: Low latency (<50ms to users)

**Docker:**
- [ ] Docker installed (20.10+)
- [ ] docker-compose installed (2.0+)
- [ ] Sufficient disk space for images

**OR Kubernetes:**
- [ ] Cluster accessible
- [ ] kubectl configured
- [ ] Ingress controller deployed
- [ ] Load balancer available

---

## Deployment

### Option A: Docker Compose (Simple)

```bash
# 1. Build image
docker-compose build

# 2. Start services
docker-compose up -d

# 3. Verify health
curl http://localhost:8000/health

# 4. Check logs
docker-compose logs -f goassist

# 5. Test API
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Checklist:**
- [ ] Image builds successfully
- [ ] All containers start
- [ ] Health check passes
- [ ] Can create session
- [ ] Logs show no errors

### Option B: Kubernetes (Production)

```bash
# 1. Apply manifests
kubectl apply -f k8s/

# 2. Check deployment
kubectl get pods -l app=goassist

# 3. Check services
kubectl get svc goassist

# 4. Check ingress
kubectl get ingress goassist

# 5. Test endpoint
curl https://your-domain.com/health
```

**Checklist:**
- [ ] Pods running (3+ replicas)
- [ ] Service exposed
- [ ] Ingress configured
- [ ] SSL certificate valid
- [ ] Health probes passing

---

## Post-Deployment

### 1. Smoke Tests ✓

**API Endpoints:**
```bash
# Health
curl https://your-domain.com/health
# Expected: {"status":"healthy",...}

# Liveness
curl https://your-domain.com/livez
# Expected: {"status":"ok"}

# Readiness
curl https://your-domain.com/readyz
# Expected: {"status":"ready",...}

# Sessions
curl -X POST https://your-domain.com/sessions \
  -H "Content-Type: application/json" \
  -d '{}'
# Expected: {"session_id":"...","state":"idle",...}
```

**Checklist:**
- [ ] All health endpoints respond
- [ ] Can create session
- [ ] Can retrieve session
- [ ] Can delete session
- [ ] Session limit enforced

### 2. Voice Flow Test ✓

**Manual test with web client:**

1. Open `examples/web-client/index.html`
2. Update API URL to production endpoint
3. Click "Connect & Start Session"
4. Allow microphone access
5. **Speak:** "Hello, can you hear me?"
6. **Verify:**
   - [ ] Session connects
   - [ ] Speech transcribed (check logs)
   - [ ] LLM responds
   - [ ] Audio synthesized
   - [ ] Hear response in browser
   - [ ] TTFA < 2000ms
   - [ ] State transitions correct

7. **Test barge-in:**
   - [ ] Interrupt while agent speaking
   - [ ] Agent stops within ~150ms
   - [ ] Can continue conversation

**Checklist:**
- [ ] End-to-end voice works
- [ ] Latency acceptable
- [ ] Barge-in responsive
- [ ] No audio glitches
- [ ] Multiple turns work

### 3. Load Test ✓

**Concurrent sessions:**
```bash
# Create 10 concurrent sessions
for i in {1..10}; do
  curl -X POST https://your-domain.com/sessions \
    -H "Content-Type: application/json" \
    -d '{}' &
done
wait
```

**Checklist:**
- [ ] Handles 10 concurrent sessions
- [ ] Handles 50 concurrent sessions
- [ ] Handles 100 concurrent sessions (if configured)
- [ ] Returns 503 when at capacity
- [ ] CPU/memory stable under load
- [ ] No memory leaks

### 4. Monitoring Setup ✓

**OpenTelemetry:**
- [ ] Traces exporting to Jaeger/OTLP
- [ ] Can view traces in UI
- [ ] Latency metrics visible
- [ ] Error traces captured

**Metrics to Track:**
- [ ] TTFA p50, p95, p99
- [ ] Barge-in latency p95
- [ ] Active sessions count
- [ ] Session success rate
- [ ] Component health (LLM, ASR, TTS)
- [ ] Error rate
- [ ] CPU/memory usage

**Alerts to Configure:**
- [ ] TTFA p95 > 2000ms
- [ ] Session capacity > 80%
- [ ] Error rate > 5%
- [ ] Health check failing
- [ ] High memory usage (>80%)
- [ ] LLM API errors

### 5. Security ✓

**CSRF Protection:**
- [ ] CSRF_ENABLED=true in production
- [ ] CSRF tokens working
- [ ] Test: POST without token fails

**Rate Limiting:**
- [ ] Rate limits active
- [ ] Test: Rapid requests throttled
- [ ] 429 response returned

**HTTPS/TLS:**
- [ ] SSL certificate valid
- [ ] Force HTTPS redirect
- [ ] HSTS header set
- [ ] Secure cookies

**Secrets:**
- [ ] API keys in secrets manager (not .env in repo)
- [ ] Secrets rotated regularly
- [ ] No secrets in logs

**Network:**
- [ ] Only necessary ports exposed
- [ ] Internal services not public
- [ ] Firewall rules configured

---

## Rollback Plan

### If Deployment Fails

**Docker Compose:**
```bash
# Stop new version
docker-compose down

# Start previous version
docker-compose up -d --force-recreate
```

**Kubernetes:**
```bash
# Rollback to previous revision
kubectl rollout undo deployment/goassist

# Check status
kubectl rollout status deployment/goassist
```

**Checklist:**
- [ ] Rollback procedure documented
- [ ] Previous version tagged
- [ ] Can rollback in <5 minutes
- [ ] Data migrations reversible

---

## Go-Live Checklist

### Before Directing Traffic

- [ ] All smoke tests pass
- [ ] Load test successful
- [ ] Monitoring active
- [ ] Alerts configured
- [ ] Rollback plan ready
- [ ] On-call engineer assigned
- [ ] Documentation updated

### Traffic Migration

**Gradual rollout recommended:**

1. **5% traffic** → Monitor 1 hour
2. **25% traffic** → Monitor 2 hours
3. **50% traffic** → Monitor 4 hours
4. **100% traffic** → Monitor 24 hours

**At each stage, verify:**
- [ ] Error rate < 1%
- [ ] TTFA p95 < 2000ms
- [ ] No critical alerts
- [ ] User feedback positive

### Post-Launch (24 hours)

- [ ] Review all metrics
- [ ] Check for anomalies
- [ ] Review error logs
- [ ] Verify billing/costs
- [ ] Document any issues
- [ ] Plan improvements

---

## Success Criteria

**Deployment is successful when:**

✅ All health checks pass
✅ Voice conversation works end-to-end
✅ TTFA p95 < 2000ms (TMF compliance)
✅ Barge-in latency < 150ms (TMF compliance)
✅ Handles target concurrent sessions (100)
✅ Error rate < 1%
✅ Monitoring active
✅ No critical issues

**Ready for production traffic!** 🚀

---

## Maintenance

### Daily

- [ ] Check error logs
- [ ] Review latency metrics
- [ ] Verify all health checks passing
- [ ] Check capacity usage

### Weekly

- [ ] Review week's metrics
- [ ] Check for memory leaks
- [ ] Update dependencies
- [ ] Review security advisories

### Monthly

- [ ] Capacity planning review
- [ ] Performance optimization
- [ ] Cost optimization
- [ ] Security audit
- [ ] Disaster recovery test

---

## Troubleshooting

See: `docs/Ops-Runbook-v3.0.md` for detailed incident response procedures.

**Common issues:**

| Issue | Solution |
|-------|----------|
| TTFA > 2000ms | Check LLM latency, TTS processing time |
| 503 errors | Increase MAX_CONCURRENT_SESSIONS or scale horizontally |
| Memory leak | Restart service, investigate session cleanup |
| LLM errors | Check API key, rate limits, endpoint health |
| No audio output | Verify TTS engine configured, check audio synthesis |
| Barge-in slow | Check VAD latency, cancellation propagation |

---

## Support

- **Documentation:** `docs/` directory
- **Issues:** https://github.com/paulhopcraft-dot/goassist3/issues
- **Ops Runbook:** `docs/Ops-Runbook-v3.0.md`
- **Docker Guide:** `DOCKER-GUIDE.md`
