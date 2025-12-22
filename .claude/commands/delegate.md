---
description: Spawn sub-agents for isolated tasks
---

Delegate specific tasks to specialized sub-agents for parallel execution and focused expertise.

## Available Agent Types

### 1. Research Agent (Explore)
**Use for**: Code exploration, pattern analysis, dependency mapping
**Example**: "Find all error handling patterns in the codebase"

### 2. Review Agent  
**Use for**: Code review, security analysis, best practices
**Example**: "Review authentication implementation for security issues"

### 3. Validator Agent
**Use for**: Independent testing, verification  
**Example**: "Run full test suite and report results"

### 4. Debug Agent
**Use for**: Issue investigation, root cause analysis
**Example**: "Investigate why TTS fallback isn't triggering"

### 5. Plan Agent
**Use for**: Architecture design, implementation planning
**Example**: "Design implementation for real-time streaming"

## Delegation Strategy

**When to delegate:**
- Task is independent and self-contained
- Need specialized focus (testing, review, research)
- Can parallelize work (spawn multiple agents)
- Want unbiased perspective (validation, review)

**How to delegate:**
1. Identify task type
2. Choose appropriate agent
3. Provide clear, focused prompt
4. Receive summary results
5. Integrate findings

## Execute Delegation

**Current task**: [Analyze user request]

**Recommended delegation**:
- Agent type: [Research/Review/Validator/Debug/Plan]
- Reason: [Why this agent is appropriate]
- Prompt: [Clear, focused instruction]

Spawn agent and report: "✅ Delegated to [agent type]. Results: [summary]"
