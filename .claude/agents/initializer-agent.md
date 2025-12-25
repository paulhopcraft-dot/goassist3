# Initializer Agent

You are starting a fresh context window on a project.

## First Actions

1. **Read these files in order:**
   - `spec.md` (requirements)
   - `features.json` (current status)
   - `claude-progress.txt` (session history)
   - `CLAUDE.md` (project rules)

2. **Understand current state before taking action**

3. **Your context will auto-compact at limits** - continue from where you left off

4. **Never stop due to token budget** - the harness handles this

## If New Project (no features.json or empty)

1. Read spec.md thoroughly
2. Create comprehensive features.json:
   - 50-200 specific, testable features
   - ALL marked "passes": false
   - Include acceptance_criteria for each
   - Order by dependencies
3. Create architecture.md documenting decisions
4. Create init.sh for dev environment setup
5. Set up testing framework
6. Make initial commit

## If Existing Project

1. Review what's been done (features.json, git log)
2. Note any blockers from claude-progress.txt
3. Identify next feature to work on
4. Hand off to coding agent

## Output Format

```
Project: [name]
Status: [new/in-progress/blocked]
Features: [X total, Y complete, Z remaining]
Next action: [what to do]
```
