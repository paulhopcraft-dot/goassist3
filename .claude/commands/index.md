---
description: Generate PROJECT_INDEX.json codebase map
---

<instructions>
Generate comprehensive codebase index for fast context loading.
</instructions>

<scan_strategy>
<source_files pattern="src/**/*.py">
- Module docstrings
- Class names and purposes
- Public functions/methods
- Key imports
</source_files>

<test_files pattern="tests/**/*.py">
- Test coverage areas
- Integration test suites
</test_files>

<config_files>
- dev.yaml, prod.yaml structure
- Key configuration sections
</config_files>

<documentation>
- README, specs, architecture docs
</documentation>
</scan_strategy>

<output_format>
<file_structure>PROJECT_INDEX.json</file_structure>
<schema>
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
</schema>
</output_format>

<execution>
Scan codebase and create PROJECT_INDEX.json with above structure.

Report: "✅ Generated PROJECT_INDEX.json ([X] files, [Y] LOC)"
</execution>
