# Quick Voice Test Guide

## Prerequisites Check

```bash
# 1. Python installed?
python --version  # Should be 3.11+

# 2. Dependencies installed?
pip list | grep fastapi  # Should show fastapi

# 3. .env file configured?
cat .env  # Check LLM_API_KEY is set
```

## Step 1: Start the Server (Terminal 1)

```bash
cd C:\dev\goassist3

# Quick start (uses .env file)
uvicorn src.main:app --reload --port 8000

# Or with explicit config
uvicorn src.main:app --reload --port 8000 \
  --env-file .env
```

**Expected output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

## Step 2: Verify Server Health

```bash
# In another terminal
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","components":{...}}
```

## Step 3: Open Test Client (Browser)

### Option A: Direct file open
```bash
# Windows
start examples/web-client/index.html

# Mac/Linux
open examples/web-client/index.html
```

### Option B: HTTP server (recommended for CORS)
```bash
cd examples/web-client
python -m http.server 8080

# Then open browser to:
# http://localhost:8080
```

## Step 4: Test Voice Conversation

1. **Click "Connect & Start Session"**
2. **Allow microphone access** (browser will prompt)
3. **Wait for "Connected"** status
4. **SPEAK INTO MICROPHONE:** "Hello, can you hear me?"
5. **LISTEN** for agent response
6. **CHECK METRICS:**
   - TTFA should be < 2000ms
   - Turns should increment
   - State should transition: listening → thinking → speaking → listening

## Step 5: Test Barge-In

1. **Start conversation**
2. **While agent is speaking, INTERRUPT** by talking
3. **Agent should stop within ~150ms**
4. **Verify** state shows "interrupted" → "listening"

## Troubleshooting

### Server won't start

**Error: "ModuleNotFoundError"**
```bash
# Install dependencies
pip install -r requirements.txt
```

**Error: "Address already in use"**
```bash
# Port 8000 is busy, use different port
uvicorn src.main:app --reload --port 8001

# Update client: Change API URL to http://localhost:8001
```

**Error: "LLM_API_KEY not set"**
```bash
# Edit .env file
echo "LLM_API_KEY=your-api-key-here" >> .env
```

### Client won't connect

**"Session creation failed: 503"**
- Server at max capacity
- Check server logs
- Try: `curl -X POST http://localhost:8000/sessions -H "Content-Type: application/json" -d "{}"`

**"Microphone access denied"**
- Check browser permissions
- Try Chrome/Edge (better WebRTC support)
- If using file://, try http server instead

**"No audio output"**
- Check server TTS_ENGINE setting in .env
- Check browser audio isn't muted
- Look for errors in browser console (F12)

### Still not working?

**Check server logs:**
```bash
# Server terminal should show:
POST /sessions → 200
POST /sessions/{id}/offer → 200
POST /sessions/{id}/ice-candidate → 200
```

**Check browser console (F12):**
```javascript
// Should see:
Microphone access granted
Session created: abc-123
WebRTC connection established
```

## Expected Performance

| Metric | Target (TMF) | Typical |
|--------|--------------|---------|
| Session creation | <500ms | ~100ms |
| WebRTC connection | <2s | ~500ms |
| TTFA (first response) | <2000ms | ~300-500ms |
| Barge-in latency | ≤150ms | ~50-100ms |

## What to Test

### Basic Functionality
- [ ] Server starts without errors
- [ ] Health endpoint responds
- [ ] Session creation works
- [ ] WebRTC connection establishes
- [ ] Can send audio
- [ ] Can receive audio
- [ ] Conversation works end-to-end

### Performance
- [ ] TTFA < 2000ms
- [ ] Multiple turns work
- [ ] Barge-in responsive (<150ms)
- [ ] No audio glitches/dropouts

### Robustness
- [ ] Can disconnect and reconnect
- [ ] Session cleanup on disconnect
- [ ] Handles network issues gracefully

## Current Limitations

⚠️ **Using Mock Components**

If .env has:
```bash
TTS_ENGINE=mock
ASR_MODEL_PATH=/test/models/asr
```

You're using **mocks**, not real voice:
- Won't actually transcribe your speech
- Won't actually synthesize audio
- Good for testing WebRTC connection only

**For REAL voice testing, configure:**
```bash
# Real ASR (Whisper)
ASR_MODEL_PATH=/path/to/whisper-model
# OR
ASR_API_URL=http://your-whisper-server

# Real TTS (Coqui)
TTS_ENGINE=coqui
# OR
TTS_ENGINE=bark

# Real LLM
LLM_API_KEY=sk-...
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4
```

## Next Steps

After basic testing works:

1. **Configure real models** (ASR, TTS, LLM)
2. **Test full voice pipeline** (speak → transcribe → generate → synthesize → hear)
3. **Measure actual latencies** over 20+ turns
4. **Test avatar** (if ENABLE_AVATAR=true)
5. **Load testing** (multiple concurrent sessions)

## Quick Verification Commands

```bash
# Health check
curl http://localhost:8000/health

# List sessions
curl http://localhost:8000/sessions

# Create session
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{}'

# Get session status
curl http://localhost:8000/sessions/{session-id}

# Delete session
curl -X DELETE http://localhost:8000/sessions/{session-id}
```

## Help

If you get stuck:
1. Check server logs (terminal running uvicorn)
2. Check browser console (F12 → Console tab)
3. Check network tab (F12 → Network tab)
4. Review `.env` configuration
5. Verify all dependencies installed
