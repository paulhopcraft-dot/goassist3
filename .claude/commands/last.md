---
description: Show the last prompt or question asked
---

<instructions>
Display the most recent user prompt/question from this session.

If available, also show:
- The last 3 prompts in reverse order
- Any commands that were executed
</instructions>

<output_format>
## Last Prompt
```
[Most recent user message]
```

## Recent History (Last 3)

1. **[timestamp/order]**: [prompt summary]
2. **[timestamp/order]**: [prompt summary]
3. **[timestamp/order]**: [prompt summary]

## Commands Executed
- `/[command]` - [brief result]
- `[bash command]` - [brief result]
</output_format>

<execution>
Review conversation history and provide the above summary.
</execution>
