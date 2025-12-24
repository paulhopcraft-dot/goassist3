---
description: Initialize project with features list and tracking files
---

<role>
You are the INITIALIZER AGENT for this project.
</role>

<instructions>
Read @spec.md thoroughly, then execute the initialization sequence.
</instructions>

<initialization_sequence>
<step number="1">
<task>Create features.json</task>
<requirements>
- Generate 50-200 specific, testable features
- Mark ALL features as "passes": false initially
- Features should be granular (e.g., "user can click login button")
- Include acceptance_criteria for each feature
- Order by dependencies
</requirements>
<note>Think hard about the feature list - be comprehensive. This determines everything.</note>
</step>

<step number="2">
<task>Create claude-progress.txt</task>
<initial_content>
Session 1 (Initializer): Set up project structure
</initial_content>
</step>

<step number="3">
<task>Create architecture.md</task>
<requirements>
- Document technical decisions
- Explain the structure
</requirements>
</step>

<step number="4">
<task>Create init.sh (if applicable)</task>
<requirements>
- Script to start dev environment
- Install dependencies
- Run smoke test
</requirements>
</step>

<step number="5">
<task>Set up testing framework</task>
<condition>If not present</condition>
</step>

<step number="6">
<task>Make initial git commit</task>
</step>
</initialization_sequence>

<output_format>
After completion, report:
- Total features created
- Recommended build order
- Any blockers or questions
</output_format>
