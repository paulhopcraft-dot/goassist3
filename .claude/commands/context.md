---
description: Check context window usage
---

Analyze current context window usage and provide recommendations.

## Context Usage Report

**Current Token Usage**: [Calculate from conversation length]
**Percentage Filled**: X%
**Remaining**: Y tokens

## Status
- [ ] Under 50% - Healthy
- [ ] 50-70% - Monitor  
- [ ] Over 70% - Consider /fresh

## Recommendations
- If >50%: "Context usage is moderate. Consider wrapping up current task."
- If >70%: "⚠️ High context usage. Recommend running /fresh to preserve state and reset context."
- If >85%: "🔴 Critical context usage. Run /fresh immediately to avoid truncation."

## Next Steps
[Provide specific recommendation based on current usage]
