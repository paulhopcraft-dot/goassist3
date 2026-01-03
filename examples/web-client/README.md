# GoAssist Web Test Client

Simple browser-based client for testing voice conversation functionality.

## Features

- ✅ Microphone access and WebRTC audio streaming
- ✅ Real-time session state display
- ✅ TTFA (Time to First Audio) measurement
- ✅ Turn counter
- ✅ Connection status monitoring
- ✅ Barge-in testing
- ✅ Full conversation logs

## Quick Start

### 1. Start the GoAssist Server

```bash
# From project root
cd C:\dev\goassist3

# Set environment variables (create .env file or export)
export LLM_API_KEY=your-api-key
export LLM_BASE_URL=https://api.openai.com/v1
export LLM_MODEL_NAME=gpt-4
export TTS_ENGINE=mock
export ASR_MODEL_PATH=/path/to/whisper
export MAX_CONCURRENT_SESSIONS=10

# Start server
uvicorn src.main:app --reload --port 8000
```

### 2. Open Test Client

```bash
# Open in browser
start examples/web-client/index.html

# Or use Python HTTP server
cd examples/web-client
python -m http.server 8080
# Then open http://localhost:8080
```

### 3. Test Voice Conversation

1. Click **"Connect & Start Session"**
2. Allow microphone access when prompted
3. Wait for "Connected" status
4. **Speak into your microphone**
5. Listen for the agent's response
6. Observe TTFA metric (should be <2000ms per TMF)

### 4. Test Barge-In

1. Start a conversation
2. While agent is speaking, **start talking**
3. Agent should stop within 150ms (per TMF)
4. Click **"Test Barge-In"** button as indicator

## Configuration

### API URL
Default: `http://localhost:8000`

Change in the UI or edit `index.html`:
```javascript
<input type="text" id="apiUrl" value="http://your-server:8000" />
```

### Audio Settings

The client uses these WebRTC audio constraints:
```javascript
audio: {
    echoCancellation: true,
    noiseSuppression: true,
    autoGainControl: true
}
```

## Metrics Displayed

| Metric | Description | Target (TMF) |
|--------|-------------|--------------|
| **Session State** | Current FSM state | - |
| **TTFA (ms)** | Time to First Audio | <2000ms |
| **Turns** | Completed conversation turns | - |

## Troubleshooting

### "Microphone access denied"
- Check browser permissions
- Use HTTPS (required for getUserMedia on non-localhost)
- Try different browser (Chrome/Edge recommended)

### "Session creation failed: 503"
- Server at capacity (check MAX_CONCURRENT_SESSIONS)
- Check server logs

### "No audio output"
- Check browser audio settings
- Verify server TTS is configured
- Check browser console for errors

### "Connection state: failed"
- Check firewall/network
- Verify server is running
- Check CORS settings if on different domain

## Browser Compatibility

**Tested:**
- ✅ Chrome 90+
- ✅ Edge 90+
- ✅ Firefox 88+

**Not Supported:**
- ❌ Safari (limited WebRTC support)
- ❌ IE 11

## Expected Behavior

### Normal Conversation Flow

1. **Status:** "Connected - Speak to begin conversation"
2. **State:** `listening`
3. **User speaks** → State: `thinking`
4. **LLM responds** → State: `speaking`
5. **Response complete** → State: `listening`

### Barge-In Flow

1. **State:** `speaking` (agent talking)
2. **User interrupts** → State: `interrupted`
3. **Cancellation completes** → State: `listening`
4. **User speaks** → State: `thinking`

## Log Messages

| Type | Color | Example |
|------|-------|---------|
| **Info** | Blue | "Requesting microphone access..." |
| **Success** | Green | "Session created: abc-123" |
| **Warning** | Yellow | "Testing barge-in..." |
| **Error** | Red | "Error: Connection failed" |

## Testing Checklist

- [ ] Microphone access granted
- [ ] Session created successfully
- [ ] WebRTC connection established
- [ ] Can speak and hear response
- [ ] TTFA < 2000ms
- [ ] Barge-in works (interrupt during speech)
- [ ] Multiple conversation turns work
- [ ] Clean disconnect

## Next Steps

After manual testing works:

1. Test with avatar enabled (ENABLE_AVATAR=true)
2. Test with production LLM
3. Measure p95 latency over 20+ turns
4. Test under load (multiple concurrent clients)

## Known Limitations

- Basic UI (functional, not polished)
- No avatar visualization
- No transcript display
- No audio level indicators
- Manual TTFA measurement (not automated)

## Files

```
examples/web-client/
├── index.html      # Main test client
└── README.md       # This file
```
