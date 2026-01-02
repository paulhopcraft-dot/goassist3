# Engineering Mode v4.0

## Core Rules (5 total)

### Rule 1: Project Context
Every response starts with:
```
[PROJECT: {folder-name}]
```
No exceptions.

### Rule 2: Progress Tracking
- Update `claude-progress.txt` after completing work
- Track features in `features.json` if it exists
- Before `/handoff`, summarize what was done

### Rule 3: Model Selection
**Default: Sonnet** (`claude --model sonnet`)

**MUST spawn Opus agent when:**
- Choosing between libraries/frameworks
- Database schema design
- API architecture decisions
- Authentication/authorization design
- Complex debugging (>30 min stuck)
- Ambiguous requirements needing interpretation
- Performance optimization trade-offs
- Any "should we use X or Y" moment

**How to spawn:** Use Task tool with `model: "opus"`

**Stay on Sonnet for:**
- Feature implementation (CRUD, services, controllers)
- Tests, refactoring, UI work
- API endpoints, routine coding

### Rule 4: Verify Before Commit
Before any git commit:
1. Run tests
2. Check for obvious issues
3. If 100+ lines changed, do a quick review

### Rule 5: Run /status After Every Task
After completing ANY task, run `/status` to:
- Show progress
- Recommend next command
- Display C/A/H menu

**No exceptions. This is how the user knows what to do next.**

---

## Auto-Triggers (5 total)

| Trigger | When | Action |
|---------|------|--------|
| **Test** | Before commit | Run test suite |
| **Review** | 100+ lines changed, security files touched | Quick code review |
| **Security** | .env or auth code modified | Check for exposed secrets |
| **Progress** | Task completed | Update claude-progress.txt |
| **Recover** | Build/test failures | Diagnose and fix |

---

## Command Reference

| Situation | Use |
|-----------|-----|
| Starting a session | `/status` |
| What should I work on? | `/continue` |
| Before committing | `/review` |
| Ending session | `/handoff` |
| 3+ similar tasks | `/autonomous` |
| New function/class | `/tdd` |
| Feature complete | `/verify` |
| New project | `/init-project` |
| Library choice | `/decide` |
| Risky change | `/anticipate` |
| Complex problem | `/think` |
| Security code | `/security-scan` |
| Multi-file change | `/branch` |
| Merge conflicts | `/resolve` |
| Important context | `/remember` |
| Forgot something | `/recall` |

Run `/help` for full list.

**After completing a task, run `/status` to show progress and next actions.**

---

## Guidelines (not rules)

**Keep it simple:**
- Don't over-engineer
- One feature at a time
- Minimal abstractions

**Be explicit:**
- If you can't verify something works, say so
- If blocked, explain why
- If unsure, ask

**Git workflow:**
- Conventional commits (feat/fix/docs/refactor)
- Commit after each feature passes
- Don't force push

---

## For Large Tasks Only

If task is >15 min estimated, show plan with model and time:
```
TASK: {description}

STEPS:
1. {step} (sonnet, ~5min)
2. {step} (opus, ~8min)
3. {step} (sonnet, ~3min)

TOTAL: ~16min | EST COST: ~$0.XX
PROCEED?
```

Skip this for small tasks. Just do the work.

---

## Session Start

On session start:
1. Check git status
2. Check for failing tests
3. Propose next action

Keep it quick. Don't run 5 commands before the user can speak.

---

That's it. 80 lines instead of 440.
