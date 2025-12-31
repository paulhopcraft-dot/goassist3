# 12-Point Avatar Realism & Utility Checklist

> Quality assurance checklist for evaluating talking avatars in GoAssist.
> Use for A/B testing during builds or demos.

## Overview

| Score | Status |
|-------|--------|
| ≥9/12 | Demo-ready |
| ≤7/12 | Needs fixes (prioritize 6,7,8,12 for utility; 2,3,5 for realism) |

---

## Checklist Items

### 1. Micro-expressions

**What**: Subtle brow/cheek twitches map to emphasis and emotion.

**Pass Criteria**: At least 2 distinct micro-moves fire within 300ms of stressed syllables (e.g., brow raise + squint) on 3/5 test lines.

**Test Method**:
- Run prosody test script
- Observe `browInnerUp`, `browOuterUp*`, `cheekSquint*` blendshapes
- Verify timing correlation with audio emphasis peaks

**Blendshapes to Monitor**: `browInnerUp`, `browOuterUpLeft`, `browOuterUpRight`, `cheekSquintLeft`, `cheekSquintRight`

---

### 2. Lip-sync Accuracy

**What**: Visemes match phonemes (p/b/m close lips; f/v show teeth; o/u show rounding).

**Pass Criteria**: ≤2 visible desyncs per 10-second read at 24-30 fps.

**Test Method**:
- Run lip-sync stressor script
- Count frame mismatches between expected viseme and rendered
- Focus on plosives (p/b/m), fricatives (f/v), and rounded vowels (o/u)

**Test Script**:
```
"Buy Bob a big blue box. Fifty vivid violets fade very fast."
```

**Critical Blendshapes**: `jawOpen`, `mouthClose`, `mouthPucker`, `mouthFunnel`, `viseme_PP`, `viseme_FF`

---

### 3. Eye Contact Consistency

**What**: Gaze anchors to listener with natural saccades.

**Pass Criteria**: 70-90% on-target gaze with 2-5 saccades per 10s; no "dead stare" >2s.

**Test Method**:
- Track `eyeLook*` blendshapes over time
- Calculate gaze deviation from center
- Count saccade events (rapid gaze shifts)
- Flag continuous fixation >2s

**Blendshapes to Monitor**: `eyeLookDownLeft`, `eyeLookDownRight`, `eyeLookInLeft`, `eyeLookInRight`, `eyeLookOutLeft`, `eyeLookOutRight`, `eyeLookUpLeft`, `eyeLookUpRight`

---

### 4. Blink Cadence

**What**: Natural blink rate (10-20/min) with situational spikes on emphasis.

**Pass Criteria**: Average 12-18 blinks/min with ≥1 blink in first 6s of a turn.

**Test Method**:
- Monitor `eyeBlink*` blendshapes
- Count blink events (value crosses 0.5 threshold)
- Calculate rate and verify first-turn blink

**Blendshapes to Monitor**: `eyeBlinkLeft`, `eyeBlinkRight`

---

### 5. Head Pose Dynamics

**What**: Micro-nods/tilts tied to sentence rhythm.

**Pass Criteria**: 1-3 small pose changes per sentence without jitter or drift.

**Test Method**:
- Track `HeadRotation` (Pitch, Yaw, Roll)
- Count pose change events per sentence boundary
- Check for unintended jitter (high-frequency oscillation)
- Check for drift (monotonic change without reset)

---

### 6. Voice-to-Lip Sync (A/V Offset)

**What**: Audio leads video slightly for perceived synchronization.

**Pass Criteria**: Absolute A/V offset ≤80ms p95 under load.

**Test Method**:
- Measure audio packet timestamp vs frame render timestamp
- Calculate offset distribution
- Verify p95 ≤80ms

**Metrics**: `av_offset_ms_p95`, `av_offset_ms_p99`

---

### 7. Turn-taking (Barge-in)

**What**: Stops speaking when interrupted; resumes gracefully.

**Pass Criteria**:
- Detects user speech and halts TTS within 150ms p95
- Resumes within 500ms after hand-off

**Test Method**:
1. Have avatar read 10-second paragraph
2. Interrupt at 3s with "Hang on—what's the price?"
3. Measure time from interrupt to TTS halt
4. Measure time from silence detection to response start

**Test Script**:
```
User: [Avatar speaking]
User: "Hang on—what's the price?"
Expected: Avatar stops within 150ms, responds within 500ms
```

---

### 8. Latency Under Load

**What**: Cold/hot paths stay responsive.

**Pass Criteria**:
- TTFA (time-to-first-audio) ≤250ms p95
- Steady-state response ≤400ms p95 with 5 concurrent sessions

**Test Method**:
- Cold start: First utterance after 30s idle
- Hot path: Continuous conversation
- Load test: 5 concurrent sessions with standardized prompts
- Measure TTFA and steady-state latency

**Metrics**: `ttfa_ms_p95`, `response_latency_ms_p95`, `concurrent_sessions`

---

### 9. Prosody & Emphasis

**What**: Stress, pitch, and pacing match intent.

**Pass Criteria**: Words flagged as emphasis receive ≥10% amplitude or pitch delta and ≤15% speed change; audibly clear in ABX test.

**Test Method**:
- Run emphasis shift test
- Analyze audio for amplitude/pitch on emphasized words
- Conduct blind ABX comparison

**Test Script** (shift emphasis each repetition):
```
"I didn't say he stole the money."
"I DIDN'T say he stole the money."
"I didn't SAY he stole the money."
"I didn't say HE stole the money."
"I didn't say he STOLE the money."
"I didn't say he stole THE money."
"I didn't say he stole the MONEY."
```

---

### 10. Content Grounding

**What**: Answers cite source or memory; avoid hallucination.

**Pass Criteria**: For 10 factual prompts, ≥9 include source tag or retrieval snippet; 0 critical hallucinations.

**Test Method**:
- Ask 10 factual questions requiring retrieval
- Verify each response includes citation/source
- Flag any fabricated facts

**Test Prompts**:
```
1. "What's our current plan price?"
2. "What are the system requirements?"
3. "Who is the primary contact for support?"
4. "What's the refund policy?"
5. "When was the last update released?"
```

---

### 11. Fallback Behaviors

**What**: Graceful degradation for ASR/TTS/LLM errors.

**Pass Criteria**:
- On ASR drop or 2s silence: display "listening" cue, ask 1-line clarify within 1s
- On retrieval miss: return "I don't have that yet" + next step

**Test Method**:
- Force ASR failure (network drop simulation)
- Force 2s silence with no input
- Query unknown information
- Verify avatar response matches fallback protocol

**Expected Fallbacks**:
| Scenario | Response |
|----------|----------|
| ASR drop | "I didn't catch that—could you say it again?" |
| 2s silence | "Are you still there?" |
| Retrieval miss | "I don't have that information yet. Would you like me to...?" |

---

### 12. Noisy-input Robustness

**What**: Handles background noise and input restarts.

**Pass Criteria**:
- With -5 dB SNR babble noise, intent correct ≥8/10
- Misfires recover with 1 clarify question

**Test Method**:
- Play café noise at -5 dB SNR
- Issue 10 test commands
- Count correct intent extractions
- Verify misfire recovery pattern

**Test Script** (with background noise):
```
"Book me Thursday 3 pm with Dr. Lee in Carlton."
```

---

## Quick Test Scripts

### Lip-sync Stressor (Plosives/Fricatives)
```
"Buy Bob a big blue box. Fifty vivid violets fade very fast."
```

### Prosody & Emphasis
```
"I didn't say he stole the money."
(Repeat, shifting emphasized word each time)
```

### Turn-taking & Barge-in
```
1. Have avatar read 10-second paragraph
2. Interrupt at 3s with "Hang on—what's the price?"
```

### Noisy Input
```
Play café noise (-5 dB SNR) while asking:
"Book me Thursday 3 pm with Dr. Lee in Carlton."
```

### Grounding Check
```
Ask three factuals requiring retrieval:
- "What's our current plan price?"
- "What are the system requirements?"
- "When was the last update released?"
```

---

## Scoring Sheet

| # | Item | Pass (1) / Fail (0) | Notes |
|---|------|---------------------|-------|
| 1 | Micro-expressions | ☐ | |
| 2 | Lip-sync accuracy | ☐ | |
| 3 | Eye contact consistency | ☐ | |
| 4 | Blink cadence | ☐ | |
| 5 | Head pose dynamics | ☐ | |
| 6 | Voice-to-lip sync (A/V offset) | ☐ | |
| 7 | Turn-taking (barge-in) | ☐ | |
| 8 | Latency under load | ☐ | |
| 9 | Prosody & emphasis | ☐ | |
| 10 | Content grounding | ☐ | |
| 11 | Fallback behaviors | ☐ | |
| 12 | Noisy-input robustness | ☐ | |
| **Total** | | **/12** | |

---

## Priority Fix Order

**If score ≤7/12:**

### Utility First (Items 6, 7, 8, 12)
1. **A/V offset** — Most noticeable to users
2. **Turn-taking** — Critical for natural conversation
3. **Latency** — Affects perceived responsiveness
4. **Noise robustness** — Required for real-world deployment

### Realism Second (Items 2, 3, 5)
1. **Lip-sync** — Most obvious visual artifact
2. **Eye contact** — Creates uncanny valley if wrong
3. **Head pose** — Adds life to static appearance

---

## Integration with GoAssist

### Automated Checks
Run the test harness:
```bash
pytest tests/avatar_qa/ -v --tb=short
```

### Manual QA Session
1. Start GoAssist backend
2. Connect MetaHuman via Live Link
3. Run through each test script
4. Fill in scoring sheet
5. Document issues in `claude-progress.txt`

### Continuous Monitoring
The following metrics are exported to Prometheus:
- `goassist_av_offset_ms` (histogram)
- `goassist_ttfa_ms` (histogram)
- `goassist_bargein_latency_ms` (histogram)
- `goassist_asr_accuracy` (gauge)
