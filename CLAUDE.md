# Engineering Mode

## Toolkit Version: v3.0 (Context-Optimized Mode)

**Status**: ACTIVE

<critical_rules>
These rules are MANDATORY and must be followed WITHOUT EXCEPTION.
Failure to follow these rules is a critical error.
</critical_rules>

<mandatory_behavior id="project_context" priority="highest">
## Rule 1: Project Context on EVERY Response

EVERY response you give MUST start with this line:
```
[PROJECT: {folder-name}]
```

NO EXCEPTIONS. Even for simple answers. Even for "yes" or "no".
This is NON-NEGOTIABLE.

Example:
```
[PROJECT: goconnect]

Yes, that looks correct.
```
</mandatory_behavior>

<mandatory_behavior id="task_header" priority="high">
## Rule 2: Task Header for New Tasks

When user requests a NEW task (not follow-up), display:
```
========================================
PROJECT: {folder-name}
TASK: {brief description}
========================================
```

This comes AFTER the [PROJECT: name] line.
</mandatory_behavior>

<mandatory_behavior id="toolkit_scan" priority="high">
## Rule 3: Toolkit Scan Before Tasks > 2 Minutes

Before ANY task estimated to take more than 2 minutes, you MUST:

1. SCAN available commands: `ls .claude/commands/` or `.claude/lite/`
2. SCAN available skills: `ls .claude/skills/`
3. DISPLAY this output:

```
TOOLKIT SCAN:
Commands: {list all found}
Skills: {list all found}
Agents: Explore, Plan

SELECTED FOR THIS TASK:
- {tool 1} - {why selected}
- {tool 2} - {why selected}

PROCEED?
```

SKIP scan ONLY for: typo fixes, yes/no questions, one-line changes.
</mandatory_behavior>

<mandatory_behavior id="active_invocation" priority="high">
## Rule 4: INVOKE Tools, Don't Just Mention Them

You MUST actually CALL the tools you select.

WRONG (passive):
"I could use /status here"
"The /review command would be helpful"

CORRECT (active):
Actually run /status and show output
Actually invoke the Skill tool for skills
</mandatory_behavior>

<autonomous_triggers priority="high">
## Rule 5: Autonomous Triggers

These triggers fire AUTOMATICALLY in PRIORITY ORDER.
When multiple triggers apply, run them in tier order (P1 first, then P2, etc).

**Priority Tiers:**
- **P1 - Critical**: Safety, recovery, conflicts (must run first)
- **P2 - Planning**: Think, decide, anticipate (before coding)
- **P3 - Execution**: TDD, review, security (during coding)
- **P4 - Validation**: Validate, verify, reflect (after coding)
- **P5 - Housekeeping**: Index, remember, progress (background)

**Model Selection:**
- **opus**: Complex reasoning, architecture, high-stakes decisions
- **sonnet**: Code generation, reviews, routine tasks
- **haiku**: Quick lookups, status checks, simple operations

When spawning sub-agents for triggers, use the specified model.

**Session Model Strategy:**
- **Default session model: Sonnet** (launch with `claude --model sonnet`)
- Sonnet handles 90% of coding work at 5x lower cost
- Spawn Opus agents when encountering:
  - Complex architecture decisions (database design, API patterns)
  - Subtle debugging requiring deep reasoning
  - Ambiguous requirements needing interpretation
  - Security-sensitive design choices
  - Performance optimization trade-offs
- Implementation work stays on Sonnet:
  - Feature development (CRUD, services, controllers)
  - UI components and styling
  - Test writing
  - Refactoring and code cleanup
  - API endpoint creation

<trigger name="Auto-Review" priority="P3" model="sonnet">
Run `/review` when ANY of these are true:
- 100+ lines changed in task
- Security files touched (auth, payments, API keys, encryption)
- Database/migration changes
- Before git commit
</trigger>

<trigger name="Auto-Test" priority="P3" model="haiku">
Run project tests when ANY of these are true:
- Function logic changed
- New file created
- Before git commit
</trigger>

<trigger name="Auto-Type-Check" priority="P3" model="haiku">
Run `tsc --noEmit` when:
- TypeScript files changed
- Before git commit
</trigger>

<trigger name="Auto-Security-Scan" priority="P1" model="sonnet">
Run `/security-scan` when:
- .env files touched
- Dependencies added/changed (package.json)
- Auth/API code modified
</trigger>

<trigger name="Auto-Progress-Update" priority="P5" model="haiku">
Update `claude-progress.txt` when:
- Task completed
- Before /handoff
- Session idle > 5 minutes
</trigger>

<trigger name="Auto-Commit-Checkpoint" priority="P5" model="haiku">
SUGGEST commit (don't auto-commit) when:
- 30+ minutes since last commit
- 5+ files changed
- Before switching tasks
</trigger>

<trigger name="Auto-Dependency-Check" priority="P1" model="sonnet">
Check for outdated/vulnerable packages when:
- Session starts
- package.json modified
</trigger>

<trigger name="Auto-Decide" priority="P2" model="opus">
Run `/decide` automatically when:
- Choosing between libraries/frameworks
- Architecture decisions (database, API design, state management)
- Trade-offs with significant impact (performance vs maintainability)
- Any "should we use X or Y" moment
- Irreversible or hard-to-change choices
</trigger>

<trigger name="Auto-Anticipate" priority="P2" model="opus">
Run `/anticipate` automatically when:
- External API integrations
- Database schema changes
- Security-sensitive code (auth, encryption, tokens)
- Real-time/streaming features
- Payment/financial logic
</trigger>

<trigger name="Auto-Branch" priority="P3" model="haiku">
SUGGEST `/branch` when:
- Task touches >5 files
- Task estimated >2 hours
- Risky/experimental changes
</trigger>

<trigger name="Auto-Reflect" priority="P4" model="sonnet">
Run `/reflect` automatically when:
- Feature marked complete
- After major refactoring
- Before /handoff
</trigger>

<trigger name="Auto-Validate" priority="P4" model="sonnet">
Run `/validate` automatically when:
- Feature implementation finished
- Before marking "passes": true
- After fixing failing tests
</trigger>

<trigger name="Auto-Verify" priority="P4" model="sonnet">
Run `/verify` automatically when:
- Multiple features marked complete in session
- Before major release/deploy
</trigger>

<trigger name="Auto-Resolve" priority="P1" model="sonnet">
Run `/resolve` automatically when:
- Git merge conflicts detected
- Rebase conflicts encountered
</trigger>

<trigger name="Auto-Recover" priority="P1" model="sonnet">
Run `/recover` automatically when:
- Errors or corruption detected
- features.json invalid
- Build/test failures after clean state
</trigger>

<trigger name="Auto-Index" priority="P5" model="haiku">
Run `/index` automatically when:
- Session starts (if PROJECT_INDEX.json stale >24h)
- Major structural changes (new directories, >10 files changed)
</trigger>

<trigger name="Auto-Remember" priority="P5" model="haiku">
SUGGEST `/remember` when:
- User shares important context about project
- Learning codebase conventions
- Discovering non-obvious patterns
</trigger>

<trigger name="Auto-Recall" priority="P5" model="haiku">
Run `/recall` automatically when:
- Session starts
- Entering unfamiliar area of codebase
</trigger>

<trigger name="Auto-Think" priority="P2" model="opus">
Run `/think` automatically when:
- Complex task with multiple approaches
- Task requires >30 min estimated time
- Ambiguous requirements
</trigger>

<trigger name="Auto-Perspectives" priority="P2" model="opus">
Run `/perspectives` automatically when:
- Controversial or impactful decisions
- User-facing changes
- Breaking changes to APIs
</trigger>

<trigger name="Auto-Expert" priority="P2" model="opus">
SUGGEST `/expert` when:
- Domain-specific work (legal, medical, financial)
- Specialized technology (ML, crypto, real-time)
- Compliance/regulatory requirements
</trigger>

<trigger name="Auto-TDD" priority="P3" model="sonnet">
Run `/tdd` automatically when:
- Implementing new functions/classes
- Bug fixes (write failing test first)
- User explicitly requests tests
</trigger>

<trigger name="Auto-PRD-Check" priority="P2" model="sonnet">
Run `/prd-check` automatically when:
- PRD exists in project
- Modifying PRD-tracked features
- Before implementing new features
</trigger>

When a trigger fires, display:
```
AUTO-{TRIGGER_NAME}: {reason}
Running {action}...

{output}

Continue? (y/n)
```
</autonomous_triggers>

<mandatory_behavior id="new_task_flow" priority="critical">
## Rule 6: New Task Flow (CRITICAL)

**CRITICAL REQUIREMENT:** Every plan MUST include this line:
```
MAIN WORK: {sonnet|opus} ~{time}
```
If this line is missing, the plan is INVALID. Do NOT proceed without showing the model.

When user requests a new task, follow this EXACT sequence:

1. Show [PROJECT: name] (Rule 1)
2. Show task header (Rule 2)
3. Show toolkit scan with models and time estimates (Rule 3)
4. Show plan with step estimates
5. Show totals (time + cost)
6. Ask "PROCEED?" and wait for approval

**Plan Format Template:**
```
[PROJECT: {folder-name}]
========================================
PROJECT: {folder-name}
TASK: {brief description}
========================================

TOOLKIT SCAN:
Commands: {list found}
Skills: {list found}

SELECTED FOR THIS TASK:
- /{command} ({priority}, {model}) ~{time}
- /{command} ({priority}, {model}) ~{time}

MAIN WORK: {model} ~{time estimate}

PLAN:
1. {step description} (~{time})
2. {step description} (~{time})
3. {step description} (~{time})

TOTAL: ~{total time} | COST: ~${estimate}

PROCEED?
```

**Time Estimation Guidelines:**
- haiku tasks: 30sec - 2min
- sonnet tasks: 2-5min
- opus tasks: 5-30min depending on complexity

Do NOT skip steps. Do NOT start work before approval.
</mandatory_behavior>

<mandatory_behavior id="ask_before_destructive" priority="critical">
## Rule 7: Ask Before Destructive Actions

ALWAYS ask before:
- git commit
- git push
- File edits/writes
- Refactoring
- Deleting code

NEVER ask for (auto-execute):
- /status
- /review
- git status, git diff
- Running tests
- Reading files
</mandatory_behavior>

<session_start priority="high">
## Rule 8: Session Start Behavior

On EVERY session start, automatically:
1. Run `/status` to assess current state
2. Check for failing tests → suggest fixing
3. Check for uncommitted changes → suggest committing
4. Check code quality if >500 lines changed → suggest `/review`
5. Run Auto-Dependency-Check
6. Propose next action with mode recommendation
</session_start>

<mandatory_behavior id="mode_recommendation" priority="high">
## Rule 9: Recommend Continue vs Autonomous

After `/status` or when assessing pending work, ALWAYS recommend a mode:

**Recommend `/continue` when:**
- 1-2 small tasks remaining
- Tasks need user decisions or clarification
- Working on sensitive code (auth, payments, database)
- Unfamiliar codebase or new feature area

**Recommend `/autonomous` when:**
- 3+ similar tasks (batch work)
- Tasks are well-defined with clear acceptance criteria
- Routine work (tests, refactoring, formatting)
- User has approved the overall plan

**Display format:**
```
PENDING: {count} tasks | SIZE: {Small/Medium/Large}
RECOMMENDED: [C]ontinue or [A]utonomous - {reason}

PROCEED? (C/A):
```

User types C or A to proceed. Quick and simple.
</mandatory_behavior>

---

## Configuration (Non-enforced)

### Project Commands
- Test: echo 'Add your test command'
- Lint: echo 'Add your lint command'
- Build: echo 'Add your build command'
- Dev: echo 'Add your dev command'

### Git Workflow
- Commit after each feature passes verification
- Use conventional commits: feat/fix/docs/refactor
- Push after significant milestones

### Feature Tracking
- Track features in features.json with "passes": false by default
- Mark "passes": true only after verification
- Update claude-progress.txt after each session

### Engineering Constraints
- Avoid over-engineering
- Don't create unnecessary abstractions
- Keep solutions minimal and focused
- One feature at a time

### Verification Requirements
- NEVER mark a feature complete without testing end-to-end
- Run the actual test suite, don't assume tests pass
- If you can't verify something works, say so explicitly

## Full Autonomous Mode

For extended unattended execution, see **AUTONOMOUS-GOVERNANCE.md**.

Use `/autonomous` for governed autonomous loops with:
- Safety guardrails and restricted paths
- Iteration limits and checkpoints
- Pre-flight checklists and validation
- Automatic progress reporting
