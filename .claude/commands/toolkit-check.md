---
description: Verify complete toolkit installation and configuration
---

<instructions>
Comprehensively check that the claude-code-toolkit is fully installed and operational in this project.
</instructions>

<validation_checklist>
<core_files>
## Core Files Validation
Check for essential toolkit files:
- [ ] `.claude/` directory exists
- [ ] `CLAUDE.md` exists and is readable
- [ ] `features.json` exists with valid JSON
- [ ] `features.schema.json` exists (for validation)
- [ ] `claude-progress.txt` exists

**Action**: Read each file and confirm structure is valid.
</core_files>

<commands>
## Slash Commands Validation
Check command installation:
- [ ] `.claude/commands/` directory exists
- [ ] Count total .md files in commands directory
- [ ] Expected: 32+ commands (v2.3 standard)

**Required Commands** (spot check):
- [ ] continue.md
- [ ] verify.md
- [ ] review.md
- [ ] prd-check.md
- [ ] tdd.md
- [ ] decide.md
- [ ] constraints.md
- [ ] perspectives.md
- [ ] help.md
- [ ] recover.md

**Action**: List all commands and confirm count ≥ 32.
</commands>

<skills>
## Skills Validation
Check skill installation:
- [ ] `.claude/skills/` directory exists
- [ ] Count skill directories
- [ ] Expected: 1+ skills (minimum: engineering-mode or frontend-design)

**Common Skills**:
- [ ] engineering-mode (global quality standards)
- [ ] frontend-design (UI design guidance)
- [ ] Project-specific skills (gpnet-healthcare, etc.)

**Action**: List all skills with their SKILL.md files.
</skills>

<agents>
## Agent System Validation (v2.3+)
Check if Advanced Agent System is installed:
- [ ] `.claude/agents/` directory exists
- [ ] `.claude/agents/registry.json` exists
- [ ] `.claude/agents/chain-engine.md` exists
- [ ] `.claude/agents/definitions/` directory exists
- [ ] Count agent definitions (expected: 3+ agents)

**Required Agent Definitions**:
- [ ] healthcare-validator.md
- [ ] test-specialist.md
- [ ] code-reviewer.md

**Registry Validation**:
- [ ] Parse registry.json for valid JSON
- [ ] Check "agents" section exists
- [ ] Check "chains" section exists
- [ ] Verify "full-verification" chain is defined

**Action**: If agents directory exists, validate all components. If not, report "Agent system not installed (optional)".
</agents>

<domain_config>
## Domain Configuration Validation
Check domain-specific configuration:
- [ ] `.claude/domain.json` exists
- [ ] Parse domain.json for valid JSON
- [ ] Validate domain type: "general" | "healthcare" | "revenue" | "finance" | "security"
- [ ] Check "agents.enabled" array exists
- [ ] Check "agents.auto_trigger" mapping exists

**Domain-Specific Files**:
- **Healthcare**: `.claude/domains/healthcare/` (evidence-schema.json, compliance-checklist.md)
- **Healthcare**: `.claude/skills/gpnet-healthcare/SKILL.md`
- **Revenue/Finance**: Financial validation settings in domain.json

**Action**: Identify domain and validate domain-specific files exist.
</domain_config>

<command_integration>
## Command-Agent Integration Validation
For projects with agent system, verify commands have agent integration:
- [ ] Read `commands/verify.md` and check for `<agent_integration>` section
- [ ] Read `commands/review.md` and check for `<trigger_agent>` tag
- [ ] Read `commands/tdd.md` and check for `<trigger_agent>` tag
- [ ] Read `commands/prd-check.md` and check for conditional healthcare agent

**Action**: Confirm commands reference agent system with fallback behavior.
</command_integration>

<version_detection>
## Toolkit Version Detection
Attempt to detect toolkit version:
- [ ] Check for agent system → v2.3+
- [ ] Check CLAUDE.md for "Agent System: ENABLED" → v2.3+
- [ ] Check for features.schema.json → v2.0+
- [ ] Check CHANGELOG.md if present in toolkit

**Action**: Report detected version (v1.0, v2.0, v2.2, v2.3).
</version_detection>
</validation_checklist>

<output_format>
```
# Toolkit Validation Report
## Project: [project name from features.json metadata]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### ✅ CORE FILES
✓ CLAUDE.md (142 lines)
✓ features.json (valid JSON, 5 features)
✓ features.schema.json (validation enabled)
✓ claude-progress.txt (3 sessions logged)

### ✅ SLASH COMMANDS
✓ 32 commands installed in .claude/commands/
  • Core: continue, status, verify, handoff
  • PRD: prd-check, build-prd, edit-prd, design-prd
  • Decision: decide, constraints, perspectives
  • Recovery: recover, validate-features, help
  • ... [list all 32]

### ✅ SKILLS
✓ 2 skills installed in .claude/skills/
  • engineering-mode (global quality standards)
  • frontend-design (distinctive UI design)

### ✅ AGENT SYSTEM (v2.3)
✓ Advanced Agent System installed
✓ Registry: 3 agents, 1 chain
  • healthcare-validator (HIPAA compliance)
  • test-specialist (test generation)
  • code-reviewer (security, quality, performance)
✓ Chain: full-verification (sequential execution)
✓ Chain engine documentation present

### ✅ DOMAIN CONFIGURATION
Domain: healthcare
Compliance: HIPAA, CMS
✓ domain.json configured with 3 agents
✓ Auto-trigger:
  • healthcare-validator: [prd-check, build-prd, verify]
  • test-specialist: [tdd, verify]
  • code-reviewer: [review, verify]
✓ Healthcare templates:
  • evidence-schema.json (audit trail schema)
  • compliance-checklist.md (HIPAA Security/Privacy)
  • skills/gpnet-healthcare/SKILL.md (PHI handling)

### ✅ COMMAND-AGENT INTEGRATION
✓ /verify → triggers full-verification chain
✓ /review → uses code-reviewer agent
✓ /tdd → uses test-specialist agent
✓ /prd-check → conditional healthcare-validator

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🎉 TOOLKIT STATUS: FULLY OPERATIONAL

**Version**: v2.3.0 (Advanced Agent System)
**Installation**: Complete (100%)
**Commands**: 32/32 available
**Skills**: 2 installed
**Agents**: 3 specialist agents + chaining
**Domain**: healthcare (HIPAA compliance automation)

**Ready for**:
✓ /project:continue - Work on next feature
✓ /verify - Full verification chain with agents
✓ /review - Expert code review
✓ /prd-check - HIPAA compliance validation

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**If issues found**:
```
# Toolkit Validation Report
## Project: [project name]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### ⚠️ ISSUES DETECTED

❌ CORE FILES
  ✗ features.json missing
  ✓ CLAUDE.md exists
  ✗ features.schema.json missing

❌ SLASH COMMANDS
  ✗ Only 4 commands found (expected 32+)
  Missing: verify, prd-check, decide, constraints, [...]

⚠️ SKILLS
  ✗ No skills installed

⚠️ AGENT SYSTEM
  ✗ Agent system not installed (optional feature)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ❌ TOOLKIT STATUS: INCOMPLETE INSTALLATION

**Action Required**:
1. Run setup wizard: bash /path/to/toolkit/setup-wizard.sh
   OR
2. Run migration: bash /path/to/toolkit/migrate-to-agents.sh

**Missing Components**:
- features.json (create with /project:init-project)
- features.schema.json (copy from toolkit/templates/)
- 28 slash commands (run setup wizard)
- Skills (optional but recommended)
- Agent system (optional, v2.3 feature)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
</output_format>

<validation_workflow>
<step number="1">
**Check Core Files**
Use Bash to check file existence:
```bash
test -f CLAUDE.md && echo "✓" || echo "✗"
test -f features.json && echo "✓" || echo "✗"
test -f features.schema.json && echo "✓" || echo "✗"
test -f claude-progress.txt && echo "✓" || echo "✗"
```
</step>

<step number="2">
**Count Commands**
```bash
ls -1 .claude/commands/*.md 2>/dev/null | wc -l
```
Expected: ≥32

List all commands:
```bash
ls .claude/commands/*.md | xargs -n1 basename | sed 's/.md$//'
```
</step>

<step number="3">
**Count Skills**
```bash
ls -1d .claude/skills/*/ 2>/dev/null | wc -l
ls -1 .claude/skills/
```
</step>

<step number="4">
**Validate Agent System**
```bash
# Check directory
test -d .claude/agents && echo "Agent system installed" || echo "Not installed (optional)"

# If installed, check components
test -f .claude/agents/registry.json && echo "✓ Registry"
test -f .claude/agents/chain-engine.md && echo "✓ Chain engine"
ls -1 .claude/agents/definitions/*.md 2>/dev/null | wc -l
```
</step>

<step number="5">
**Parse Domain Configuration**
If `.claude/domain.json` exists:
```bash
cat .claude/domain.json | grep -E '"domain"|"enabled"|"auto_trigger"'
```
Identify domain type and enabled agents.
</step>

<step number="6">
**Check Domain-Specific Files**
If domain === "healthcare":
- Check `.claude/domains/healthcare/evidence-schema.json`
- Check `.claude/domains/healthcare/compliance-checklist.md`
- Check `.claude/skills/gpnet-healthcare/SKILL.md`

If domain === "revenue" or "finance":
- Check domain.json has "financial_validation" section
</step>

<step number="7">
**Detect Version**
Logic:
- If agent system installed → v2.3+
- If features.schema.json exists → v2.0+
- Otherwise → v1.0
</step>

<step number="8">
**Generate Report**
Compile all findings into formatted report.
Use ✓ for success, ✗ for failure, ⚠️ for warnings.
Provide actionable next steps if issues found.
</step>
</validation_workflow>

<success_criteria>
**Fully Operational** requires:
- ✅ All core files present
- ✅ 32+ commands installed
- ✅ At least 1 skill installed (recommended)
- ✅ features.json has valid JSON structure
- ✅ CLAUDE.md is readable

**Agent System (v2.3+)** is optional but if present requires:
- ✅ registry.json with valid JSON
- ✅ 3+ agent definitions
- ✅ chain-engine.md documentation
- ✅ domain.json with agent configuration
</success_criteria>

<troubleshooting>
## Common Issues

**Issue**: "Only 4 commands found"
**Fix**: Run `bash /path/to/toolkit/setup-wizard.sh` to install all commands

**Issue**: "features.json missing"
**Fix**: Create manually or run `/project:init-project`

**Issue**: "Agent system not installed"
**Fix**: Optional feature. Run `bash /path/to/toolkit/migrate-to-agents.sh` to install

**Issue**: "domain.json missing"
**Fix**: Agent system not installed. Optional for v2.3.

**Issue**: "Skills directory empty"
**Fix**: Copy skills from toolkit:
```bash
cp -r /path/to/toolkit/skills/* .claude/skills/
```
</troubleshooting>
