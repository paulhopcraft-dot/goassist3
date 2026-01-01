# GoAssist Ops & Deployment Runbook v3.0 (RunPod + GPU Hosts)

**Status:** Operations reality (Derived from TMF v3.0; conservative)  
**Version:** 3.0  
**Date:** December 22, 2025

---

## 0. Purpose

This runbook describes how to deploy, operate, and recover GoAssist in production-like environments.

**It is an ops document, not a product pitch.**  
- It contains deployment details, ports, health checks, restart policy, and monitoring.
- It does not define user-facing features (PRD) or architecture truth (TMF).

---

## 1. Deployment Profiles

GoAssist supports three operational profiles. Pick one intentionally.

**PRD mode mapping:**
- **Profile A** → PRD Voice Mode (section 4.1)
- **Profile B, C** → PRD Avatar Mode (section 4.2)

### Profile A — Voice-Only (Inference Only)
- Best for scale (many concurrent voice sessions)
- No server-side rendering
- Optional client UI + transcript

**Runs:** Gateway + Orchestrator + ASR + LLM + TTS  
**Optional:** facial animation stream (for client-side avatar)

### Profile B — Avatar via Client Rendering (Recommended for scale)
- Server emits ARKit-52 blendshapes
- Client renders avatar locally
- Avoids server-side video encoding bottlenecks

**Runs:** same as Profile A + facial animation service

### Profile C — Server-Rendered Avatar (Unreal / Pixel Streaming)
- Highest server-side visual fidelity
- Lowest concurrency per GPU due to rendering + encoding limits

**Runs:** Profile A/B plus separate render runtime

---

## 2. Pod / Node Types

### 2.1 Inference Pod (required)
Runs:
- WebRTC audio gateway
- session orchestrator
- streaming ASR
- shared-model LLM serving
- streaming TTS
- (optional) facial animation engine

### 2.2 Render Pod (optional; Profile C only)
Runs:
- Unreal avatar runtime
- ingest bridge (UDP/Live Link)
- optional local facial animation (if you co-locate it)

**Hard rule:** Render Pod failures must not block Inference Pod audio.

---

## 3. Hardware Guidance (reference, not promises)

### 3.1 Reference baseline
- 2× RTX 4090 class node for “one box demo/prod”
- Keep 20GB working VRAM cap per GPU for stability

### 3.2 Concurrency reality (practical)
- Voice sessions scale with shared LLM batching; measure and tune.
- Server-rendered avatar sessions scale poorly; plan to cap or use client rendering.

**Concurrency tuning guidance:**

| Metric to Measure | Target Value | Action if Exceeded |
|-------------------|--------------|-------------------|
| TTFA p95 | ≤ 300ms | Reduce `max_concurrent_sessions` |
| GPU utilization | < 85% | Safe to increase sessions |
| LLM queue depth | < 5 | Safe to increase sessions |
| VRAM usage | < 18GB (of 20GB cap) | Safe to increase sessions |

**Tunable parameters:**
- `MAX_CONCURRENT_SESSIONS` — start at 5, increase by 2 until TTFA p95 > 300ms
- `LLM_MAX_BATCH_SIZE` — default 8, reduce if queue depth spikes
- `LLM_MAX_CONTEXT_TOKENS` — reduce from 8192 to 4096 to fit more sessions

**Tuning procedure:**
1. Start with conservative settings (5 sessions, 8192 context)
2. Run 30-minute load test at target concurrency
3. Check metrics against table above
4. Adjust one parameter at a time, re-test
5. Document final values in deployment config

This runbook does not promise a fixed session number without measured load tests.

---

## 4. Ports & Networking

### 4.1 Inference Pod
Default ports (document actual values in deployment config if changed):
- `8081` — HTTP API (health, metrics, admin backplane)
- `9000-9200/udp` — WebRTC media (depends on your gateway/SFU)
- `9464` — Prometheus metrics (optional)

**Source of truth:** If ports differ from defaults, document in `deploy/config.yaml` or equivalent deployment manifest.

### 4.2 Render Pod (Profile C)
- `8080` — Pixel Streaming / WebRTC video
- `11111/udp` — UE Live Link ingest (example)
- `9465` — metrics (optional)

### 4.3 TURN/STUN
For real networks, you will need TURN.
- Keep TURN creds out of git.
- Prefer managed TURN for reliability unless you operate it well.

---

## 5. Storage Layout (persistent)

Mount a persistent volume at `/workspace` (or similar) and keep:
- `/workspace/models/` — model weights (ASR, LLM, TTS, animation)
- `/workspace/logs/` — structured logs
- `/workspace/data/` — tenant knowledge base artifacts (if local)
- `/workspace/config/` — runtime configs

---

## 6. Configuration

### 6.1 Environment variables (Inference Pod)
Example `.env` (conceptual):

```bash
# API
API_HOST=0.0.0.0
API_PORT=8081
LOG_LEVEL=INFO

# Session
MAX_CONCURRENT_SESSIONS=25
SESSION_IDLE_TIMEOUT_S=300

# LLM
LLM_MODEL_PATH=/workspace/models/llm/mistral-7b-awq
LLM_MAX_CONTEXT_TOKENS=8192
LLM_PREFIX_CACHING=true
LLM_VRAM_CAP_GB=20

# ASR
ASR_MODEL_PATH=/workspace/models/asr/<streaming-asr-model>
VAD_ENGINE=silero

# TTS
TTS_ENGINE=<streaming-tts-engine>
TTS_MODEL_PATH=/workspace/models/tts/<tts-model>
AUDIO_PACKET_MS=20
AUDIO_OVERLAP_MS=5

# Animation (optional)
ANIMATION_ENABLED=true
ANIMATION_ENGINE=audio2face
ANIMATION_FALLBACK=lam
ANIMATION_DROP_IF_LAG_MS=120
ANIMATION_SLOW_FREEZE_MS=150

# WebRTC
WEBRTC_STUN_SERVER=stun:stun.l.google.com:19302
WEBRTC_TURN_SERVER=turn:<your-turn>:3478
WEBRTC_TURN_USERNAME=<user>
WEBRTC_TURN_PASSWORD=<pass>
```

#### Environment Variable Requirements

| Variable | Required | Valid Range | Default | Error Behavior |
|----------|----------|-------------|---------|----------------|
| **API** |||||
| `API_HOST` | Optional | Valid IP or `0.0.0.0` | `0.0.0.0` | Use default |
| `API_PORT` | Optional | 1024–65535 | `8081` | Use default |
| `LOG_LEVEL` | Optional | `DEBUG`, `INFO`, `WARN`, `ERROR` | `INFO` | Use default |
| **Session** |||||
| `MAX_CONCURRENT_SESSIONS` | Required | 1–100 (GPU-dependent) | — | Fail startup with config error |
| `SESSION_IDLE_TIMEOUT_S` | Optional | 60–3600 | `300` | Use default |
| **LLM** |||||
| `LLM_MODEL_PATH` | Required | Valid file path | — | Fail startup: "LLM model not found" |
| `LLM_MAX_CONTEXT_TOKENS` | Optional | 1024–8192 | `8192` | Use default (per TMF v3.0 section 3.2) |
| `LLM_PREFIX_CACHING` | Optional | `true`, `false` | `true` | Use default |
| `LLM_VRAM_CAP_GB` | Optional | 8–80 (GPU-dependent) | `20` | Use default; warn if exceeds available |
| **ASR** |||||
| `ASR_MODEL_PATH` | Required | Valid file path | — | Fail startup: "ASR model not found" |
| `VAD_ENGINE` | Optional | `silero`, `webrtc` | `silero` | Use default |
| **TTS** |||||
| `TTS_ENGINE` | Required | Engine identifier | — | Fail startup: "TTS engine not specified" |
| `TTS_MODEL_PATH` | Required | Valid file path | — | Fail startup: "TTS model not found" |
| `AUDIO_PACKET_MS` | Optional | 10–40 | `20` | Use default (per TMF v3.0 section 3.1) |
| `AUDIO_OVERLAP_MS` | Optional | 0–20 | `5` | Use default |
| **Animation** |||||
| `ANIMATION_ENABLED` | Optional | `true`, `false` | `true` | Use default |
| `ANIMATION_ENGINE` | Conditional | `audio2face`, `lam` | `audio2face` | Required if `ANIMATION_ENABLED=true` |
| `ANIMATION_FALLBACK` | Optional | `lam`, `none` | `lam` | Use default |
| `ANIMATION_DROP_IF_LAG_MS` | Optional | 50–200 | `120` | Use default |
| `ANIMATION_SLOW_FREEZE_MS` | Optional | 100–300 | `150` | Use default (per TMF v3.0 section 4.3) |
| **WebRTC** |||||
| `WEBRTC_STUN_SERVER` | Optional | Valid STUN URI | `stun:stun.l.google.com:19302` | Use default |
| `WEBRTC_TURN_SERVER` | Optional | Valid TURN URI | — | Skip TURN if unset |
| `WEBRTC_TURN_USERNAME` | Conditional | Non-empty string | — | Required if `WEBRTC_TURN_SERVER` set; fail startup if missing |
| `WEBRTC_TURN_PASSWORD` | Conditional | Non-empty string | — | Required if `WEBRTC_TURN_SERVER` set; fail startup if missing |

**Notes:**
- "Required" variables must be set or startup fails with a clear error message.
- "Conditional" variables are required only when their parent feature is enabled.
- All paths are validated at startup; missing files cause immediate failure with actionable error.

### 6.2 Render Pod env (Profile C)
- UE project path
- resolution / fps targets
- pixel streaming ports
- ingest port for blendshapes

Keep render config separate from inference.

---

## 7. RunPod Deployment (Conservative)

### 7.1 Prereqs
- RunPod account + API key
- SSH keypair
- Domain + DNS if exposing public endpoints
- TURN credentials if doing real WebRTC over the internet

### 7.2 Local tools (optional)
```bash
sudo apt update
sudo apt install -y git curl wget ssh
pip install runpodctl
runpodctl config set-api-key YOUR_API_KEY
```

### 7.3 Create an Inference Pod (CLI example)
```bash
runpodctl create pod \
  --name goassist-inference \
  --gpu-type "RTX 4090" \
  --gpu-count 1 \
  --disk-size 120 \
  --cpu-count 8 \
  --memory 32 \
  --image "nvidia/cuda:12.1.0-devel-ubuntu22.04" \
  --ports "8081/http,9464/http"
```

### 7.4 (Optional) Create a Render Pod
```bash
runpodctl create pod \
  --name goassist-render \
  --gpu-type "RTX 4090" \
  --gpu-count 1 \
  --disk-size 200 \
  --cpu-count 8 \
  --memory 32 \
  --image "nvidia/cuda:12.1.0-devel-ubuntu22.04" \
  --ports "8080/http,9465/http"
```

---

## 8. Provisioning the Pod

### 8.1 Bootstrap
```bash
sudo apt update
sudo apt install -y git python3 python3-pip ffmpeg
```

### 8.2 Pull repo
```bash
cd /workspace
git clone <your-repo-url> goassist
cd goassist
```

### 8.3 Python environment (example)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

### 8.4 Download models (conservative approach)
Store all models under `/workspace/models/`.

Provide a `scripts/download_models.sh` that:
- downloads LLM weights
- downloads ASR model
- downloads TTS model
- downloads animation model assets (if separate)

**Rule:** Never download into ephemeral container layers. Always to the persistent volume.

**Container volume strategy:**

When using containers (Docker, Kubernetes):
1. **Mount `/workspace/models` as external volume** — models must persist across container restarts
2. **Container image must NOT include model weights** — keeps image small (~2GB vs 30GB+)
3. **Use init container or entrypoint script** to verify models exist before starting main process

```yaml
# Example docker-compose volume mount
volumes:
  - /data/goassist/models:/workspace/models:ro
  - /data/goassist/logs:/workspace/logs:rw
```

**Volume requirements:**
| Path | Size | Mode | Purpose |
|------|------|------|---------|
| `/workspace/models` | 30-50GB | read-only | LLM, ASR, TTS, animation weights |
| `/workspace/logs` | 10GB+ | read-write | Application logs |
| `/workspace/cache` | 5GB | read-write | Prefix cache, temp files |

---

## 9. Starting Services

You can run GoAssist with either:
- **docker-compose** (recommended if you already containerized services)
- **systemd** (simple restart behavior, one host)

### 9.1 systemd example (Inference)
Create a service that restarts automatically.

```bash
cat > /etc/systemd/system/goassist-inference.service << 'EOF'
[Unit]
Description=GoAssist Inference Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/workspace/goassist
EnvironmentFile=/workspace/goassist/.env
ExecStart=/workspace/goassist/.venv/bin/python -m src.main_inference
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable goassist-inference
systemctl start goassist-inference
systemctl status goassist-inference
```

### 9.2 Health checks
- `http://<pod-ip>:8081/healthz`
- `http://<pod-ip>:8081/readyz`
- `http://<pod-ip>:8081/metrics` (if enabled)

---

## 10. Monitoring & Alerts

### 10.1 Minimum dashboards
- TTFA p50/p95
- barge-in latency p50/p95
- session count + queue depth
- GPU VRAM usage + fragmentation hints
- audio packet loss/jitter (WebRTC stats)
- animation drop/slow-freeze counts

### 10.2 Alert suggestions
- TTFA p95 > 400ms for >5 minutes
- barge-in p95 > 250ms for >2 minutes
- VRAM usage within 1GB of cap
- crash loop (restart count > 3 per hour, configurable via `ALERT_CRASH_LOOP_THRESHOLD`)

---

## 11. Recovery Procedures

### Recovery Authority Matrix

| Procedure | Authorized Role | Approval Required | Escalation Contact |
|-----------|-----------------|-------------------|-------------------|
| Safe restart (11.1) | On-call engineer | No | SRE lead if >2 restarts/hour |
| Animation disable (11.2) | On-call engineer | No | Engineering lead if >1 hour |
| LLM service restart (11.3) | On-call engineer | No | SRE lead if auto-restart fails |
| Force session termination | On-call engineer | Yes (SRE lead) | Engineering director |
| Full node restart | SRE lead | Yes (Engineering lead) | Engineering director |
| Rollback deployment | SRE lead | No | Engineering director if >30 min |
| Data recovery | Engineering lead | Yes (Engineering director) | CTO |

**Rules:**
- On-call engineer may execute "No approval" procedures autonomously during incidents
- Procedures requiring approval: contact approver via PagerDuty; if no response in 15 minutes, escalate
- All recovery actions must be logged in incident channel with timestamp and outcome
- Post-incident review required for any procedure executed more than twice in 24 hours

### 11.1 Safe restart (Inference)
- stop accepting new sessions
- allow active sessions to end or force cancel
- restart service
- confirm readiness

### 11.2 If animation is unhealthy
- disable animation (feature flag)
- keep voice mode alive
- investigate separately

### 11.3 If LLM service is unhealthy
- reject new sessions
- return explicit “service unavailable” speech
- auto-restart the model server
- preserve logs/metrics for incident

---

## 12. Scaling (Conservative)

### 12.1 Horizontal scaling
- deploy multiple inference pods
- route sessions with sticky session routing
- keep each session state local to its pod unless you build a shared session store

### 12.2 Multi-session per pod
- enable shared-model batching
- enforce backpressure policy (drop visuals first)
- cap max concurrent sessions and queue depth

### 12.3 Avatar scale note
Server-rendered avatars do not scale well on consumer GPUs.
For many concurrent agents:
- prefer client-side avatar rendering (Profile B)
- or cap server-rendered avatar sessions aggressively

---

## 13. Cost Notes (Ops-only)

Cloud GPU pricing changes often. Treat any numbers as *estimates* and re-check before budgeting.

A conservative budgeting model:
- cost per GPU-hour + storage + egress
- plus overhead for idle headroom (to keep latency stable)

---

## 14. Runbook Checklists

### 14.1 Pre-launch checklist
- [ ] TURN configured and tested on a real network
- [ ] TTFA and barge-in measured (p50/p95) under load
- [ ] 2h soak pass
- [ ] Monitoring dashboards live
- [ ] Logs stored persistently
- [ ] Avatar degradation verified (voice continues)
  - **Verification method:** Run automated test script `scripts/test_avatar_degradation.sh` OR manual procedure below
  - **Manual procedure:** (1) Start voice session with avatar enabled, (2) Kill animation service process, (3) Confirm voice output continues within 150ms, (4) Confirm avatar freezes gracefully (slow-freeze per TMF 4.3)
  - **Pass criteria:** Voice TTFA remains ≤ 250ms p95 when avatar drops; no audio interruption; graceful visual freeze

### 14.2 24h soak checklist
Per TMF v3.0 section 7.3: 24h mixed-load operation, 30% active duty cycle.
- [ ] 24h soak run recorded
- [ ] No VRAM creep beyond threshold
- [ ] No increasing TTFA drift
- [ ] Restarts are not required to remain stable

