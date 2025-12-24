---
description: Thinking mode selector based on task complexity
---

<instructions>
Select appropriate thinking depth based on task complexity.
</instructions>

<thinking_modes>
<mode name="think" tokens="4000">
<best_for>Simple fixes, typos</best_for>
<example_tasks>Bug fix, config change, docs update</example_tasks>
</mode>

<mode name="think hard" tokens="8000">
<best_for>Multi-file changes</best_for>
<example_tasks>Feature addition, refactor</example_tasks>
</mode>

<mode name="think harder" tokens="16000">
<best_for>Architecture, debugging</best_for>
<example_tasks>System design, complex bugs</example_tasks>
</mode>

<mode name="ultrathink" tokens="32000">
<best_for>Planning, research, failures</best_for>
<example_tasks>Project planning, investigation</example_tasks>
</mode>
</thinking_modes>

<decision_guide>
<use_think tokens="4K">
- Single file changes
- Clear, well-defined task
- Following established patterns
</use_think>

<use_think_hard tokens="8K">
- Multiple file coordination
- Need to understand relationships
- Some ambiguity in requirements
</use_think_hard>

<use_think_harder tokens="16K">
- Architectural decisions
- Complex debugging
- Design patterns
- Need to consider alternatives
</use_think_harder>

<use_ultrathink tokens="32K">
- First request of session
- Previous attempt failed
- Research/exploration needed
- Planning multi-step implementation
</use_ultrathink>
</decision_guide>

<recommendation>
<analysis>
[Analyze user's request and recommend mode based on above criteria]
</analysis>

<output>
"For this task, I recommend: **[mode]** because [reason]"
</output>
</recommendation>

<escalation_rule>
If a task fails with current mode, automatically escalate:
think → think hard → think harder → ultrathink
</escalation_rule>
