# Kyutai Voice Models Analysis for GoAssist3

**Date:** December 2025
**Environment:** No GPU available (benchmark pending)

## Executive Summary

**Recommendation: Evaluate Kyutai TTS as TTS replacement; Keep current ASR pipeline**

Kyutai's models show promise for GoAssist3 integration, particularly the TTS component. However, their full-duplex Moshi model is architecturally incompatible with GoAssist3's modular pipeline design.

---

## Models Evaluated

### 1. Moshi (Full-Duplex Speech-to-Speech)
- **Version:** 0.2.11 (July 2025)
- **Architecture:** 7B parameter model + Mimi codec
- **Latency:** 160-200ms theoretical/practical
- **License:** CC-BY 4.0 (commercial OK)
- **GPU Requirement:** 24GB VRAM

### 2. Kyutai TTS (Delayed Streams Modeling)
- **Version:** 1.6B parameters
- **TTFA:** 220ms first-chunk latency
- **Languages:** English, French
- **Voice Cloning:** 10-second reference audio
- **Streaming:** Text-streaming input (pipes from LLM)

### 3. Kyutai STT
- **Models:** 1B (500ms delay) / 2.6B (2.5s delay)
- **Languages:** English, French
- **Streaming:** Real-time with partial results

---

## GoAssist3 Requirements Comparison

| Requirement | GoAssist3 TMF | Moshi | Kyutai TTS | Kyutai STT |
|-------------|---------------|-------|------------|------------|
| TTFA ≤250ms p95 | Required | 200ms ✅ | 220ms ✅ | N/A |
| Barge-in ≤150ms | Required | ❓ Undocumented | ❓ Unknown | N/A |
| Streaming partials | Required | N/A | N/A | 500ms ❌ |
| Hard cancel API | Required | ❌ Not exposed | ❓ Unknown | N/A |
| Modular pipeline | Required | ❌ End-to-end | ✅ Standalone | ✅ Standalone |
| Commercial license | Required | ✅ CC-BY 4.0 | ✅ CC-BY 4.0 | ✅ CC-BY 4.0 |

---

## Detailed Analysis

### Moshi (Full-Duplex Model)

**Pros:**
- State-of-the-art full-duplex conversation
- 200ms practical latency on L4 GPU
- Handles both input and output in one model
- "Inner monologue" improves generation quality

**Cons:**
- **Black box architecture** - No access to intermediate states
- **No documented barge-in API** - Full-duplex doesn't mean interruptible
- **Incompatible with GoAssist3** - Replaces entire pipeline, not pluggable
- **24GB VRAM minimum** - Single model consumes full GPU
- **No explicit cancel mechanism** - Can't meet 150ms barge-in contract

**Verdict:** ❌ **NOT RECOMMENDED** for GoAssist3 integration

### Kyutai TTS

**Pros:**
- 220ms TTFA meets GoAssist3's 250ms requirement
- **Streaming text input** - Pipes directly from LLM output
- Voice cloning with 10-second samples
- Standalone module (fits modular architecture)

**Cons:**
- No documented cancellation/barge-in API
- Requires separate benchmark to verify cancel latency
- Newer (less battle-tested than Moshi)

**Verdict:** ✅ **WORTH TESTING** - Run GPU benchmark to verify cancel latency

### Kyutai STT

**Pros:**
- Streaming transcription support
- Semantic VAD included
- Word-level timestamps

**Cons:**
- **500ms minimum delay** - Too slow for barge-in detection
- GoAssist3 requires partial results faster than 500ms
- Deepgram Nova-2 is likely faster for real-time use

**Verdict:** ❌ **NOT RECOMMENDED** - Keep Deepgram/Whisper for ASR

---

## Benchmark Script

Created: `benchmarks/kyutai_tts_benchmark.py`

To run on GPU:
```bash
cd /home/user/goassist3
python benchmarks/kyutai_tts_benchmark.py --runs 10 --install
```

The script measures:
- TTFA (Time to First Audio)
- Total synthesis time
- Real-time factor
- GoAssist3 TMF compliance

---

## Integration Path (If Benchmarks Pass)

### Phase 1: TTS Evaluation
1. Run `kyutai_tts_benchmark.py` on GPU system
2. Verify TTFA p95 < 250ms
3. Add cancel latency test (target < 150ms)
4. Compare audio quality with current TTS

### Phase 2: Implementation
If benchmarks pass, implement Kyutai TTS as pluggable engine:

```python
# src/audio/tts/kyutai_tts.py
class KyutaiTTSEngine(BaseTTSEngine):
    """Kyutai TTS implementation.

    Uses delayed-streams-modeling for ultra-low latency.
    """

    async def synthesize_stream(
        self, text_stream: AsyncIterator[str]
    ) -> AsyncIterator[bytes]:
        # Pipe LLM output directly to Kyutai TTS
        async for chunk in kyutai_tts_stream(text_stream):
            if self._cancelled:
                break
            yield chunk

    async def cancel(self) -> None:
        # Must complete within 150ms
        await self._kyutai_cancel()
        self._cancelled = True
```

---

## Alternative: Gradium (December 2025)

Gradium (Kyutai spinoff, launched Dec 2, 2025) explicitly targets <150ms latency. However:
- Commercial API only (no self-hosted)
- No public benchmarks yet
- Monitor for future open-source release

---

## Conclusion

| Component | Recommendation | Action |
|-----------|---------------|--------|
| **ASR** | Keep Deepgram | No change needed |
| **TTS** | Test Kyutai TTS | Run GPU benchmark |
| **Full S2S** | Skip Moshi | Incompatible architecture |
| **Future** | Watch Gradium | Monitor for open-source |

**Next Steps:**
1. Run benchmark on GPU-equipped system
2. If Kyutai TTS passes, implement as pluggable engine
3. Update TTS settings to allow engine selection:
   ```
   TTS_ENGINE=kyutai
   TTS_MODEL_PATH=kyutai/tts-1.6b-en_fr
   ```
