# Backpressure Recovery Guide

## Overview

GoAssist implements **graceful degradation** under load using a 5-level backpressure system. This document explains how backpressure levels are triggered, what they do, and **how to recover** from degraded states back to NORMAL.

**Reference**: TMF v3.0 §5.2, Implementation v3.0 §5.3

---

## Backpressure Levels

```
NORMAL (0)           ← No degradation, full functionality
    ↓
ANIMATION_YIELD (1)  ← Drop avatar frames, audio continues
    ↓
VERBOSITY_REDUCE (2) ← Shorter LLM responses (70% verbosity)
    ↓
TOOL_REFUSE (3)      ← Disable non-essential tool calls
    ↓
SESSION_QUEUE (4)    ← Queue new sessions
    ↓
SESSION_REJECT (5)   ← Reject new sessions (last resort)
```

**Core Principle**: **Audio continuity ALWAYS wins** - we NEVER degrade audio quality or interrupt conversations.

---

## Level Triggers & Effects

### Level 1: ANIMATION_YIELD
**Triggers** (any of):
- Animation lag > 120ms (TMF §4.3)
- VRAM usage > 85%

**Effects**:
- ✅ Audio: UNCHANGED
- ⚠️ Animation: Drops frames, reduces framerate
- ✅ LLM: UNCHANGED
- ✅ Sessions: New sessions allowed

**Recovery**: Reduce GPU load or animation lag below 120ms

---

### Level 2: VERBOSITY_REDUCE
**Triggers** (any of):
- TTFA > 200ms (80% of 250ms contract)
- VRAM usage > 90%
- Active sessions >= MAX - 2

**Effects**:
- ✅ Audio: UNCHANGED
- ⚠️ Animation: Frames dropped (from Level 1)
- ⚠️ LLM: `max_tokens` reduced to 384 (from 512)
- ⚠️ LLM: Verbosity factor 0.7 (SCOS policy)
- ✅ Sessions: New sessions allowed

**Recovery**: Reduce TTFA below 200ms, free up VRAM, or reduce active sessions

---

### Level 3: TOOL_REFUSE
**Triggers** (any of):
- TTFA > 225ms (90% of contract)
- VRAM usage > 93%

**Effects**:
- ✅ Audio: UNCHANGED
- ⚠️ Animation: Frames dropped (from Level 1)
- ⚠️ LLM: `max_tokens` reduced to 256
- ⚠️ LLM: Verbosity factor 0.5 (very concise)
- ❌ Tools: Non-essential tools disabled
- ✅ Tools: Essential tools still work (`cancel`, `end_session`, `emergency_stop`)
- ✅ Sessions: New sessions allowed

**Recovery**: Reduce TTFA below 225ms or free up VRAM

---

### Level 4: SESSION_QUEUE
**Triggers** (any of):
- TTFA > 240ms (96% of contract)
- VRAM usage > 95%
- Active sessions >= MAX - 1

**Effects**:
- ✅ Audio: UNCHANGED (existing sessions)
- ⚠️ Animation: Frames dropped
- ⚠️ LLM: Very concise (from Level 3)
- ❌ Tools: Non-essential tools disabled
- ⚠️ Sessions: **New sessions QUEUED**

**Recovery**: Complete active sessions, reduce VRAM usage, or improve TTFA

---

### Level 5: SESSION_REJECT ⚠️
**Triggers** (any of):
- TTFA >= 250ms (AT contract limit!)
- VRAM usage > 98%
- Active sessions >= MAX
- Error rate > 5%

**Effects**:
- ✅ Audio: UNCHANGED (existing sessions)
- ⚠️ Animation: Frames dropped
- ⚠️ LLM: Very concise
- ❌ Tools: Non-essential tools disabled
- ❌ Sessions: **New sessions REJECTED** (HTTP 503)

**Recovery**: See detailed recovery steps below

---

## Recovery Flow: SESSION_REJECT → NORMAL

### Step 1: Identify the Trigger
Check logs for backpressure activation:
```json
{
  "event": "backpressure.level_activated",
  "level": "SESSION_REJECT",
  "trigger": "ttfa=252ms, vram=99%, sessions=10"
}
```

### Step 2: Address Root Cause

#### If Triggered by TTFA >= 250ms:
```bash
# Check current TTFA
curl http://localhost:8081/metrics | grep goassist_ttfa

# Actions:
1. Reduce concurrent sessions (ends oldest sessions)
2. Check vLLM GPU utilization
3. Verify network latency to vLLM server
4. Check if LLM server is throttling
```

#### If Triggered by VRAM > 98%:
```bash
# Check GPU memory
nvidia-smi

# Actions:
1. End idle sessions: DELETE /sessions/{session_id}
2. Reduce MAX_CONCURRENT_SESSIONS in config
3. Check for memory leaks (session cleanup)
4. Restart vLLM server if fragmented
```

#### If Triggered by Active Sessions >= MAX:
```bash
# Check active sessions
curl http://localhost:8081/sessions

# Actions:
1. Wait for sessions to complete naturally
2. Or: gracefully end idle sessions
3. Increase MAX_CONCURRENT_SESSIONS (if GPU allows)
```

#### If Triggered by Error Rate > 5%:
```bash
# Check error logs
tail -f logs/goassist.log | grep -i error

# Actions:
1. Identify failing component (ASR, LLM, TTS, Animation)
2. Check service health: GET /readyz
3. Restart failing service
4. Check for cascading failures
```

### Step 3: Monitor Metrics Improvement
```bash
# Watch metrics decrease
watch -n 1 'curl -s http://localhost:8081/metrics | grep -E "(ttfa|vram|active_sessions)"'
```

### Step 4: Observe Automatic Recovery
The `BackpressureController` automatically downgrades levels when thresholds are no longer exceeded:

```
SESSION_REJECT (5)  → metrics improve
    ↓
SESSION_QUEUE (4)   → sessions complete, VRAM drops
    ↓
TOOL_REFUSE (3)     → TTFA improves to 220ms
    ↓
VERBOSITY_REDUCE (2)→ TTFA improves to 190ms
    ↓
ANIMATION_YIELD (1) → VRAM drops to 82%
    ↓
NORMAL (0)          ← Full functionality restored ✅
```

**Note**: Recovery happens **automatically** at 1-second intervals as metrics improve.

---

## Recovery Time Estimates

| From Level | To Normal | Typical Time | Actions Required |
|------------|-----------|--------------|------------------|
| ANIMATION_YIELD | NORMAL | 5-10 seconds | Passive (animation catches up) |
| VERBOSITY_REDUCE | NORMAL | 10-30 seconds | End 1-2 sessions |
| TOOL_REFUSE | NORMAL | 30-60 seconds | End 2-3 sessions or restart vLLM |
| SESSION_QUEUE | NORMAL | 1-3 minutes | Let queued sessions complete |
| SESSION_REJECT | NORMAL | 3-10 minutes | Active intervention required |

---

## Manual Recovery Commands

### Check Current Backpressure State
```bash
# Via metrics endpoint
curl http://localhost:8081/metrics | grep backpressure

# Via session endpoint (includes backpressure info)
curl http://localhost:8081/sessions
```

### Force Session Cleanup
```bash
# List all sessions
curl http://localhost:8081/sessions | jq '.sessions[] | {id: .session_id, state: .state}'

# End specific session
curl -X DELETE http://localhost:8081/sessions/{session_id}

# End all idle sessions (shell script)
for sid in $(curl -s http://localhost:8081/sessions | jq -r '.sessions[] | select(.state=="idle") | .session_id'); do
  curl -X DELETE "http://localhost:8081/sessions/$sid"
done
```

### Restart vLLM Server (If Needed)
```bash
# SSH to RunPod
ssh root@<runpod-ip>

# Check vLLM health
curl http://localhost:8000/health

# Restart vLLM
systemctl restart vllm
# Or: kill vllm process and restart

# Verify restart
curl http://localhost:8000/health
```

### Adjust MAX_CONCURRENT_SESSIONS
```bash
# Edit .env
nano .env

# Change:
MAX_CONCURRENT_SESSIONS=10  # Reduce from 100 if needed

# Restart GoAssist
systemctl restart goassist
```

---

## Prevention Strategies

### 1. Capacity Planning
- **Monitor trending**: Track TTFA, VRAM, session count over time
- **Set alerts**: Prometheus alerts at Level 2 (VERBOSITY_REDUCE)
- **Load testing**: Use `tests/test_load_concurrent_sessions.py`

### 2. Auto-Scaling
```python
# Future enhancement: Auto-scale based on backpressure
if backpressure_controller.level >= BackpressureLevel.SESSION_QUEUE:
    spawn_new_vllm_instance()
```

### 3. Circuit Breakers
- Automatically reject requests at Level 5
- Return `HTTP 503 Service Unavailable` with `Retry-After` header
- Client should back off and retry

### 4. Session Limits
```python
# Set per-user session limits
MAX_SESSIONS_PER_USER = 2

# Set session idle timeout
SESSION_IDLE_TIMEOUT_S = 300  # 5 minutes
```

---

## Monitoring & Alerting

### Key Metrics to Monitor
```promql
# TTFA approaching contract limit
goassist_ttfa_p95 > 200  # Warning
goassist_ttfa_p95 > 240  # Critical

# VRAM usage high
goassist_vram_usage_pct > 90  # Warning
goassist_vram_usage_pct > 95  # Critical

# Backpressure active
goassist_backpressure_level > 0

# Sessions at capacity
goassist_active_sessions >= goassist_max_sessions - 2
```

### Prometheus Alert Examples
```yaml
- alert: BackpressureLevelHigh
  expr: goassist_backpressure_level >= 3
  for: 2m
  annotations:
    summary: "Backpressure level {{ $value }} active"
    description: "System under high load, degrading quality"

- alert: SessionsAtCapacity
  expr: goassist_active_sessions >= goassist_max_sessions - 1
  for: 1m
  annotations:
    summary: "Sessions at capacity"
    description: "Consider scaling or ending idle sessions"
```

---

## Testing Recovery

```python
# Test automatic recovery
python -m pytest tests/test_backpressure.py::TestBackpressureController::test_auto_recovery

# Simulate high load
python -m pytest tests/test_load_concurrent_sessions.py::test_create_100_sessions
```

---

## FAQ

### Q: Why doesn't backpressure recover immediately?
**A**: Recovery is automatic but gradual. The controller checks metrics every 1 second. If thresholds are still exceeded, the level stays active. Recovery happens when metrics drop below thresholds.

### Q: Can I manually reset backpressure to NORMAL?
**A**: No. Backpressure is driven by actual system metrics. Forcing it to NORMAL without fixing the underlying issue would violate TMF contracts (TTFA, barge-in latency).

### Q: What if recovery takes too long?
**A**: This indicates persistent resource exhaustion. Solutions:
1. Reduce concurrent sessions
2. Scale horizontally (add more vLLM instances)
3. Upgrade GPU (more VRAM)
4. Optimize LLM model (quantization, smaller model)

### Q: Does backpressure affect existing sessions?
**A**: Existing sessions get degraded quality (shorter responses, no animation) but audio continues. Only Level 5 affects new sessions (rejection).

### Q: How do I disable backpressure for testing?
**A**: Don't. Backpressure prevents cascading failures. For testing, use mock components or increase resource limits.

---

## Related Documentation
- [TMF v3.0](../docs/TMF-v3.0.md) - Performance contracts
- [Implementation v3.0](../docs/Implementation-v3.0.md) §5.3 - Backpressure policy
- [Ops Runbook v3.0](../docs/Ops-Runbook-v3.0.md) §9 - Operations playbook
- [CODING-STANDARDS.md](./CODING-STANDARDS.md) - Code patterns

---

**Version**: 1.0
**Last Updated**: 2026-01-02
**Author**: GoAssist v3.0 Team
