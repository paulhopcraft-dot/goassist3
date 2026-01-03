# Cloud API Quick Start Guide

Test voice conversation in **10 minutes** using cloud APIs - no GPU required!

## Why Cloud APIs?

**Fastest path to test voice conversation:**
- ✅ No model downloads (~15GB)
- ✅ No GPU/RunPod instance needed
- ✅ Pay-per-use (cheap for testing: ~$0.50 for 100 turns)
- ✅ Test voice UX today, optimize for cost later

## Prerequisites

**API Keys needed:**
1. **Anthropic API Key** (LLM) - https://console.anthropic.com/
2. **Deepgram API Key** (ASR) - https://console.deepgram.com/
3. **ElevenLabs API Key** (TTS) - https://elevenlabs.io/

**Alternative:** Use existing OpenAI key for all three (GPT-4 + Whisper + TTS)

## Setup (5 minutes)

### 1. Install Cloud API Dependencies

```bash
cd C:\dev\goassist3

# Install anthropic and elevenlabs packages
pip install anthropic>=0.18.0 elevenlabs>=1.0.0
```

### 2. Configure Environment

Create/edit `.env` file:

```bash
# Core
ENVIRONMENT=development
MAX_CONCURRENT_SESSIONS=10

# LLM: Anthropic Claude (Best for conversation)
LLM_ENGINE=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here
ANTHROPIC_MODEL=claude-sonnet-3-5-20241022

# ASR: Deepgram (Streaming speech recognition)
DEEPGRAM_API_KEY=your-deepgram-key-here

# TTS: ElevenLabs (High-quality voice synthesis)
TTS_ENGINE=elevenlabs
ELEVENLABS_API_KEY=your-elevenlabs-key-here
ELEVENLABS_VOICE_ID=EXAVITQu4vr4xnSDxMaL  # Sarah (default)

# Optional: Disable avatar for faster testing
ANIMATION_ENABLED=false

# Security (can disable for local testing)
CSRF_ENABLED=false
```

### 3. Start Server

```bash
# Using Docker (recommended)
docker-compose up

# Or directly with Python
uvicorn src.main:app --reload --port 8000
```

### 4. Open Test Client

```bash
# Browser-based test client
start examples\web-client\index.html

# Or use HTTP server
cd examples/web-client
python -m http.server 8080
# Then open http://localhost:8080
```

## Test Voice Conversation

1. Click **"Connect & Start Session"**
2. Allow microphone access
3. **SPEAK:** "Hello, how are you?"
4. **LISTEN** for response
5. **CHECK METRICS:**
   - TTFA should be < 2000ms
   - State should transition: listening → thinking → speaking
6. **TEST BARGE-IN:** Interrupt while agent is speaking

## Expected Costs (Pay-Per-Use)

**Per 100 conversation turns:**
- Anthropic Claude Sonnet: ~$0.30
- Deepgram ASR (3 min audio): ~$3.00
- ElevenLabs TTS: ~$5.00
- **Total: ~$8.30 per 100 turns**

**For quick testing (10 turns): ~$0.83**

## Troubleshooting

### "ANTHROPIC_API_KEY not set"

Make sure `.env` file exists and has:
```bash
ANTHROPIC_API_KEY=sk-ant-...
```

Restart server after changing `.env`.

### "elevenlabs package not installed"

```bash
pip install elevenlabs>=1.0.0
```

### "Deepgram API connection error"

Check your Deepgram API key is valid:
```bash
curl https://api.deepgram.com/v1/listen \
  -H "Authorization: Token YOUR_KEY" \
  -H "Content-Type: application/json"
```

### No audio output

1. Check browser console (F12) for errors
2. Verify ElevenLabs API key is valid
3. Check TTS_ENGINE=elevenlabs in .env
4. Check server logs for TTS errors

## Alternative: All OpenAI Stack

If you already have an OpenAI API key:

```bash
# .env
LLM_ENGINE=vllm  # Use existing vLLM client (OpenAI-compatible)
LLM_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=sk-...

# ASR: OpenAI Whisper API (need to add support)
# TTS: OpenAI TTS API (need to add support)
```

**Note:** We haven't added OpenAI Whisper/TTS yet (only vLLM for LLM). Would need ~15 min to add.

## After Voice Testing Works

Once you've validated the voice conversation flow:

### Option A: Keep Using Cloud APIs (Simplest)
- Easy scaling (no infrastructure)
- Pay only for usage
- Good for moderate traffic (<1000 sessions/day)

### Option B: Migrate to RunPod (Lower Cost at Scale)
- Self-hosted LLM (no per-token fees)
- Local TTS (no per-character fees)
- Keep Deepgram for ASR (hard to beat)
- See: RUNPOD-DEPLOYMENT.md (to be created)

### Option C: Hybrid (Recommended)
- **Development/Testing:** Cloud APIs
- **Production:** RunPod + local models
- Best of both worlds

## Voice Quality Comparison

| Provider | Quality | Latency | Cost |
|----------|---------|---------|------|
| **ElevenLabs** | Excellent | ~500ms TTFA | $0.18/1K chars |
| **OpenAI TTS** | Very Good | ~400ms TTFA | $0.015/1K chars |
| **XTTS-v2 (local)** | Good | ~300ms TTFA | Free (GPU cost) |
| **Kyutai (local)** | Experimental | ~200ms TTFA | Free (GPU cost) |

For **testing:** Start with ElevenLabs (best quality)
For **production:** Evaluate cost vs quality trade-offs

## Next Steps

After validating voice works:

1. **Measure real-world performance:**
   - Run 20+ conversation turns
   - Track TTFA p95
   - Test barge-in responsiveness
   - Verify audio quality acceptable

2. **Decision point:**
   - Voice works great? → Deploy to staging
   - Voice needs improvement? → Iterate on prompts/settings
   - Costs too high? → Migrate to RunPod

3. **Production hardening:**
   - Set up monitoring (Jaeger)
   - Configure rate limits
   - Add error recovery
   - Set up alerts

## Support

- **Test client guide:** `examples/web-client/README.md`
- **Docker deployment:** `DOCKER-GUIDE.md`
- **Production checklist:** `DEPLOYMENT-CHECKLIST.md`
- **Issues:** https://github.com/paulhopcraft-dot/goassist3/issues

---

**Goal:** Get voice conversation working end-to-end **today** with minimal setup. Then optimize for cost/infrastructure later.
