---
description: Check context window usage
---

<instructions>
Analyze current context window usage and provide recommendations.
</instructions>

<context_usage_report>
<metrics>
**Current Token Usage**: [Calculate from conversation length]
**Percentage Filled**: X%
**Remaining**: Y tokens
</metrics>

<status>
- [ ] Under 50% - Healthy
- [ ] 50-70% - Monitor
- [ ] Over 70% - Consider /fresh
</status>
</context_usage_report>

<recommendations>
<threshold level="50-70%">
"Context usage is moderate. Consider wrapping up current task."
</threshold>

<threshold level="70-85%">
"⚠️ High context usage. Recommend running /fresh to preserve state and reset context."
</threshold>

<threshold level="85-100%">
"🔴 Critical context usage. Run /fresh immediately to avoid truncation."
</threshold>
</recommendations>

<next_steps>
[Provide specific recommendation based on current usage]
</next_steps>
