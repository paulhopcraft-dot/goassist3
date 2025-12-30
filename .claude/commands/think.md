---
description: Thinking mode selector based on task complexity
---

Select appropriate thinking depth based on task complexity.

## Thinking Modes

| Mode | Tokens | Best For | Example Tasks |
|------|--------|----------|---------------|
| **think** | ~4,000 | Simple fixes, typos | Bug fix, config change, docs update |
| **think hard** | ~8,000 | Multi-file changes | Feature addition, refactor |
| **think harder** | ~16,000 | Architecture, debugging | System design, complex bugs |
| **ultrathink** | ~32,000 | Planning, research, failures | Project planning, investigation |

## Decision Guide

**Use think** (4K):
- Single file changes
- Clear, well-defined task
- Following established patterns

**Use think hard** (8K):  
- Multiple file coordination
- Need to understand relationships
- Some ambiguity in requirements

**Use think harder** (16K):
- Architectural decisions
- Complex debugging
- Design patterns
- Need to consider alternatives

**Use ultrathink** (32K):
- First request of session
- Previous attempt failed
- Research/exploration needed
- Planning multi-step implementation

## Current Recommendation
[Analyze user's request and recommend mode based on above criteria]

"For this task, I recommend: **[mode]** because [reason]"

## Escalation Rule
If a task fails with current mode, automatically escalate:
think → think hard → think harder → ultrathink
