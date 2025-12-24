---
description: Spawn sub-agents for isolated tasks
---

<instructions>
Delegate specific tasks to specialized sub-agents for parallel execution and focused expertise.
</instructions>

<available_agent_types>
<agent type="Research" alias="Explore">
<use_for>Code exploration, pattern analysis, dependency mapping</use_for>
<example>Find all error handling patterns in the codebase</example>
</agent>

<agent type="Review">
<use_for>Code review, security analysis, best practices</use_for>
<example>Review authentication implementation for security issues</example>
</agent>

<agent type="Validator">
<use_for>Independent testing, verification</use_for>
<example>Run full test suite and report results</example>
</agent>

<agent type="Debug">
<use_for>Issue investigation, root cause analysis</use_for>
<example>Investigate why TTS fallback isn't triggering</example>
</agent>

<agent type="Plan">
<use_for>Architecture design, implementation planning</use_for>
<example>Design implementation for real-time streaming</example>
</agent>
</available_agent_types>

<delegation_strategy>
<when_to_delegate>
- Task is independent and self-contained
- Need specialized focus (testing, review, research)
- Can parallelize work (spawn multiple agents)
- Want unbiased perspective (validation, review)
</when_to_delegate>

<how_to_delegate>
<step number="1">Identify task type</step>
<step number="2">Choose appropriate agent</step>
<step number="3">Provide clear, focused prompt</step>
<step number="4">Receive summary results</step>
<step number="5">Integrate findings</step>
</how_to_delegate>
</delegation_strategy>

<execution>
<analysis>
**Current task**: [Analyze user request]

**Recommended delegation**:
- Agent type: [Research/Review/Validator/Debug/Plan]
- Reason: [Why this agent is appropriate]
- Prompt: [Clear, focused instruction]
</analysis>

<result>
Spawn agent and report: "✅ Delegated to [agent type]. Results: [summary]"
</result>
</execution>
