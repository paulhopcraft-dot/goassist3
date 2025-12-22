---
description: Generate PROJECT_INDEX.json codebase map
---

Generate comprehensive codebase index for fast context loading.

## Scan Strategy
1. **Source files** (src/**/*.py)
   - Module docstrings
   - Class names and purposes
   - Public functions/methods
   - Key imports

2. **Test files** (tests/**/*.py)
   - Test coverage areas
   - Integration test suites

3. **Config files**
   - dev.yaml, prod.yaml structure
   - Key configuration sections

4. **Documentation**
   - README, specs, architecture docs

## Output Format: PROJECT_INDEX.json

```json
{
  "generated": "YYYY-MM-DD HH:MM",
  "stats": {
    "total_files": X,
    "total_lines": Y,
    "source_files": A,
    "test_files": B
  },
  "modules": {
    "src/audio/pipeline.py": {
      "purpose": "Voice pipeline orchestration",
      "classes": ["VoicePipeline"],
      "key_functions": ["process_audio", "initialize"],
      "imports": ["ASREngine", "TTSEngine", "LLMRouter"],
      "lines": 352
    }
  },
  "architecture": {
    "pipeline_flow": "Audio → ASR → SCOS → RAG → LLM → TTS",
    "key_components": [...]
  }
}
```

## Generate Index
Scan codebase and create PROJECT_INDEX.json with above structure.

Report: "✅ Generated PROJECT_INDEX.json ([X] files, [Y] LOC)"
