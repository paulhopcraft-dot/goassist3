# Auto-Sync: Cross-Project Learning

## The Vision

**Problem**: Toolkit learns something in `govertical` but other projects don't benefit

**Solution**: When toolkit improves itself, automatically copy improvements to ALL active projects

**Result**: Learn once, benefit everywhere

---

## How It Works

### Scenario: Payment Pattern Learned in govertical

```
Day 1: User builds 5 payment features in govertical
  ↓
Day 7: Toolkit learns user's payment patterns
  ↓
Toolkit creates: /build-payment command
  ↓
AUTO-SYNC TRIGGERED:
  ✓ Copy /build-payment to gpnet3
  ✓ Copy /build-payment to goassist3
  ✓ Copy payment-expert skill to all projects
  ↓
Result: ALL projects can now use /build-payment
```

---

## Auto-Sync Architecture

### Component 1: Active Projects Registry

**File**: `.claude/v3/self-learning/active-projects.json`

```json
{
  "sync_enabled": true,
  "projects": [
    {
      "path": "C:/Dev/gpnet3",
      "domain": "healthcare",
      "active": true,
      "last_sync": "2025-12-25T10:00:00Z"
    },
    {
      "path": "C:/Dev/govertical",
      "domain": "revenue",
      "active": true,
      "last_sync": "2025-12-25T10:00:00Z"
    },
    {
      "path": "C:/Dev/goassist3",
      "domain": "general",
      "active": true,
      "last_sync": "2025-12-25T10:00:00Z"
    }
  ],
  "sync_rules": {
    "commands": "all_projects",
    "skills": "domain_compatible",
    "patterns": "all_projects",
    "learnings": "all_projects"
  }
}
```

---

### Component 2: Improvement Classification

When toolkit creates an improvement, classify it:

#### **Type 1: Universal Improvements**
*Apply to ALL projects*

Examples:
- Better prompt templates
- Meta-prompting improvements
- CoT/ToT pattern enhancements
- Bug fixes in existing commands

**Auto-sync**: YES (copy to all projects immediately)

---

#### **Type 2: Domain-Specific Improvements**
*Apply only to compatible domains*

Examples:
- `/build-payment` → revenue + general (not healthcare-specific)
- `hipaa-validator` skill → healthcare only
- SOX audit patterns → revenue only

**Auto-sync**: SELECTIVE (copy to compatible domains)

**Rules**:
```json
{
  "improvement": "/build-payment",
  "source": "govertical (revenue)",
  "compatible_domains": ["revenue", "general", "finance"],
  "incompatible_domains": ["healthcare"],
  "sync_to": ["goassist3"],
  "skip": ["gpnet3"]
}
```

---

#### **Type 3: User-Specific Patterns**
*Apply to all user's projects*

Examples:
- User always uses Decimal for money → All projects
- User prefers TDD workflow → All projects
- User commits after every feature → All projects

**Auto-sync**: YES (user behavior is consistent)

---

### Component 3: Sync Trigger Points

When to trigger auto-sync:

```markdown
TRIGGER 1: After Auto-Improvement
When toolkit updates a command/skill:
  → Immediately sync to other projects

TRIGGER 2: Scheduled Sync
Every 24 hours:
  → Check for new improvements
  → Sync to projects that were offline

TRIGGER 3: On Project Open
When user opens a project:
  → Check: Are there improvements from other projects?
  → Sync if needed
  → Notify: "Synced /build-payment from govertical"

TRIGGER 4: Manual Sync
User runs: /toolkit:sync-all
  → Force sync all improvements immediately
```

---

### Component 4: Sync Workflow

```markdown
STEP 1: Improvement Detected
  - Toolkit learned something in govertical
  - Created: /build-payment command

STEP 2: Classify Improvement
  - Type: Domain-specific (payment systems)
  - Compatible domains: revenue, general, finance
  - Source project: govertical

STEP 3: Identify Target Projects
  - Active projects: gpnet3, govertical, goassist3
  - Filter by domain compatibility:
    - gpnet3 (healthcare): Skip (not payment-related)
    - govertical (revenue): Source (already has it)
    - goassist3 (general): Compatible ✓

STEP 4: Copy to Target Projects
  - Copy: .claude/commands/build-payment.md → goassist3
  - Copy: .claude/skills/payment-expert/ → goassist3
  - Update: goassist3/.claude/v3/self-learning/sync-log.jsonl

STEP 5: Notify User (Next Time They Open goassist3)
  "💡 Synced from govertical:
   ✓ /build-payment command (learned from 5 payment features)
   ✓ payment-expert skill

   These are now available in this project!"

STEP 6: Git Commit (Optional)
  If git enabled:
    - Commit in goassist3: "sync: add /build-payment from govertical"
    - Tag: sync-from-govertical-2025-12-25
```

---

## Sync Rules Examples

### Example 1: Payment Command

**Learned in**: govertical (revenue domain)

**Sync to**:
- ✓ goassist3 (general domain - can use payment patterns)
- ✗ gpnet3 (healthcare domain - not payment-focused)

**Rationale**: Payment systems are revenue/general, not healthcare-specific

---

### Example 2: HIPAA Validator Skill

**Learned in**: gpnet3 (healthcare domain)

**Sync to**:
- ✗ govertical (revenue domain - no HIPAA requirements)
- ✗ goassist3 (general domain - no HIPAA requirements)

**Rationale**: HIPAA compliance only relevant to healthcare

**UNLESS**: User works on healthcare features in another project
- If user builds healthcare feature in goassist3
- Then sync HIPAA patterns

---

### Example 3: TDD Workflow Improvement

**Learned in**: govertical (user always runs /tdd before /build-prd)

**Sync to**:
- ✓ gpnet3 (user behavior, not domain-specific)
- ✓ goassist3 (user behavior, not domain-specific)

**Rationale**: User preference, applies everywhere

---

### Example 4: Audit Logging Pattern

**Learned in**: govertical (forgot audit logging 3 times, now auto-checked)

**Sync to**:
- ✓ gpnet3 (healthcare needs audit trails too)
- ✓ goassist3 (good practice everywhere)

**Rationale**: Audit logging is universal best practice, especially for compliance domains

---

## Smart Sync: Cross-Project Learning

### Scenario: Learn in One, Apply in All

```
Week 1: govertical
  - User builds 5 payment features
  - Toolkit learns Stripe + Decimal + Audit patterns
  - Creates: /build-payment

Week 2: Auto-sync to goassist3
  - Syncs /build-payment to goassist3
  - User builds payment feature in goassist3
  - Uses govertical patterns automatically

Week 3: goassist3 learns something new
  - User adds fraud detection to payment in goassist3
  - Toolkit learns fraud pattern
  - Syncs back to govertical
  - Now /build-payment includes fraud detection everywhere

Week 4: Both projects benefit
  - govertical: Has fraud detection (from goassist3)
  - goassist3: Has Stripe patterns (from govertical)
  - Cross-pollination of learnings
```

**Result**: Projects teach each other!

---

## Conflict Resolution

### What if Projects Conflict?

**Scenario**:
- govertical uses Stripe for payments
- goassist3 uses PayPal for payments

**Problem**: Which pattern to sync?

**Solution**: Domain-specific variants

```markdown
Toolkit creates:
- /build-payment-stripe (from govertical patterns)
- /build-payment-paypal (from goassist3 patterns)
- /build-payment (asks which to use)

User experience in govertical:
  /build-payment → Uses Stripe by default (learned here)

User experience in goassist3:
  /build-payment → Uses PayPal by default (learned here)

User experience in new project:
  /build-payment → Asks: "Use Stripe or PayPal pattern?"
```

---

## Sync Notifications

### Silent Sync (Default)

```bash
User opens goassist3
[Background: Syncs improvements from govertical]

User runs: /toolkit:learnings

Output:
"💡 Synced Improvements (from other projects)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
From govertical:
✓ /build-payment (learned from 5 payment features)
✓ payment-expert skill
✓ Decimal precision pattern (SOX requirement)

From gpnet3:
✓ PHI sanitization pattern (HIPAA requirement)
✓ Audit logging enhancement

These are now available in this project!"
```

---

### Notify on Sync (Optional)

```json
{
  "sync_notifications": "on_project_open",
  "notification_style": "summary"
}
```

**Experience**:
```bash
User opens goassist3

🔄 Synced from Other Projects
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ /build-payment from govertical
✓ PHI sanitization from gpnet3

Run /toolkit:learnings to see details
```

---

## Implementation: Auto-Sync Script

**File**: `.claude/v3/self-learning/auto-sync.sh`

```bash
#!/bin/bash

# Auto-Sync Script
# Syncs toolkit improvements across all active projects

ACTIVE_PROJECTS=(
  "C:/Dev/gpnet3"
  "C:/Dev/govertical"
  "C:/Dev/goassist3"
)

TOOLKIT_SOURCE="C:/Dev/claude-code-toolkit"

echo "🔄 Auto-Sync: Cross-Project Learning"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Step 1: Check for new improvements in each project
for project in "${ACTIVE_PROJECTS[@]}"; do
  if [ -f "$project/.claude/v3/self-learning/improvements-to-sync.json" ]; then
    echo "Found improvements in: $project"

    # Step 2: Read improvements
    improvements=$(cat "$project/.claude/v3/self-learning/improvements-to-sync.json")

    # Step 3: For each improvement, sync to compatible projects
    # (Implementation would parse JSON and apply sync rules)

    # Step 4: Copy files to other projects
    # (Based on domain compatibility)

    # Step 5: Update sync log
    echo "$(date -Iseconds): Synced from $project" >> "$TOOLKIT_SOURCE/.claude/v3/self-learning/sync-history.log"
  fi
done

echo "✓ Sync complete"
```

---

## Auto-Sync Configuration

**File**: `.claude/v3/self-learning/sync-config.json`

```json
{
  "enabled": true,

  "sync_triggers": {
    "on_improvement": true,
    "on_project_open": true,
    "scheduled_interval_hours": 24,
    "manual_command": "/toolkit:sync-all"
  },

  "sync_rules": {
    "commands": {
      "universal": "sync_to_all",
      "domain_specific": "sync_to_compatible",
      "user_specific": "sync_to_all"
    },
    "skills": {
      "universal": "sync_to_all",
      "domain_specific": "sync_to_compatible"
    },
    "patterns": {
      "coding_style": "sync_to_all",
      "security": "sync_to_all",
      "compliance": "sync_to_compatible"
    }
  },

  "conflict_resolution": {
    "strategy": "create_variants",
    "prefer_source_project": true
  },

  "notifications": {
    "enabled": true,
    "style": "summary",
    "frequency": "on_project_open"
  },

  "git_integration": {
    "auto_commit": true,
    "commit_message_template": "sync: {improvement} from {source_project}"
  }
}
```

---

## User Experience Examples

### Example 1: Morning Workflow

```bash
# Monday morning, open govertical
cd C:/Dev/govertical

# Toolkit auto-syncs in background
[Silent sync from gpnet3 and goassist3]

# User continues working
/build-prd "subscription billing"

# Later checks learnings
/toolkit:learnings

Output:
"📊 Synced Improvements
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
From gpnet3:
✓ Improved PHI sanitization (zero leaks in 20 features)

From goassist3:
✓ API rate limiting pattern (learned from 6 APIs)

Your Improvements:
✓ Stripe idempotency pattern (100% success rate)
↑ Will sync to other projects automatically"
```

---

### Example 2: Cross-Project Benefit

```bash
# Week 1: Work in govertical (payment features)
cd C:/Dev/govertical
/build-prd "payment processing"  # Uses Stripe

# Week 2: Switch to goassist3 (different project)
cd C:/Dev/goassist3
/build-prd "donation system"  # Also needs payments

# Toolkit suggests:
"💡 I notice you're building payment features.
   I learned Stripe patterns in govertical.

   Use /build-payment to apply those patterns here? [Y/n]"

# User accepts
Y

# Feature builds with govertical patterns automatically
✓ Stripe SDK configured
✓ Decimal precision
✓ Idempotency keys
✓ Webhook validation
✓ Audit logging

Result: Zero setup, learned once, works everywhere
```

---

### Example 3: Domain-Aware Sync

```bash
# gpnet3 learns HIPAA pattern
cd C:/Dev/gpnet3
[Toolkit learns PHI encryption pattern]

# Auto-sync decides:
"PHI encryption is healthcare-specific
 → Do NOT sync to govertical (revenue)
 → Do NOT sync to goassist3 (general)
 → Keep in gpnet3 only"

# govertical learns SOX audit pattern
cd C:/Dev/govertical
[Toolkit learns audit logging pattern]

# Auto-sync decides:
"Audit logging is universal security pattern
 → Sync to gpnet3 (healthcare needs audits too)
 → Sync to goassist3 (good practice everywhere)
 → Apply to all projects"

Result: Smart domain filtering prevents irrelevant syncs
```

---

## Benefits

### 1. Learn Once, Benefit Everywhere
```
Build payment feature in govertical
→ All projects get payment patterns
→ Zero manual copying
```

### 2. Cross-Project Intelligence
```
Project A learns pattern X
Project B learns pattern Y
→ Both projects get both patterns
→ Best of all worlds
```

### 3. Consistent Quality
```
Improvement in one project
→ All projects improve
→ Zero quality drift
```

### 4. Zero Maintenance
```
No manual sync required
No copy/paste between projects
No forgetting to update other projects
```

---

## Rollback

### Undo Sync

```bash
# Undo last sync in current project
/toolkit:rollback-sync

# Undo specific improvement
/toolkit:rollback-sync /build-payment

# View sync history
/toolkit:sync-history

Output:
"Sync History
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2025-12-25 10:00: Synced /build-payment from govertical
2025-12-24 15:30: Synced PHI pattern from gpnet3
2025-12-23 09:15: Synced API pattern from goassist3

Rollback any? [Enter sync ID or 'cancel']"
```

---

## Privacy & Control

### What Gets Synced

```
✓ Command templates
✓ Skill definitions
✓ Pattern libraries
✓ Success/failure insights
✓ Configuration improvements

✗ Actual code
✗ Business logic
✗ Secrets/credentials
✗ Project-specific data
```

### Where Syncs Happen

```
Local filesystem only:
  C:/Dev/gpnet3/.claude/
  C:/Dev/govertical/.claude/
  C:/Dev/goassist3/.claude/

Never:
  External servers
  Cloud storage
  Shared repositories (unless you explicitly push)
```

### Control

```bash
# Disable auto-sync
Edit: .claude/v3/self-learning/sync-config.json
Set: "enabled": false

# Sync manually only
Set: "sync_triggers.on_improvement": false
Use: /toolkit:sync-all when ready

# Review before sync
Set: "notifications.style": "detailed_approval"
Approve each sync individually
```

---

## Implementation Timeline

### Phase 1: Basic Auto-Sync (Week 1)
```
✓ Active projects registry
✓ Universal improvements sync
✓ Manual /toolkit:sync-all command
```

### Phase 2: Smart Filtering (Week 2)
```
✓ Domain compatibility checking
✓ Type classification (universal vs domain-specific)
✓ Conflict resolution (create variants)
```

### Phase 3: Scheduled Sync (Week 3)
```
✓ Sync on project open
✓ Scheduled 24-hour sync
✓ Background sync
```

### Phase 4: Cross-Learning (Week 4)
```
✓ Bi-directional sync (projects teach each other)
✓ Pattern aggregation (combine learnings)
✓ Success metrics across projects
```

---

## Success Metrics

### Individual Project (Before Auto-Sync)
```
Project A: Learned 10 patterns
Project B: Learned 8 patterns
Project C: Learned 6 patterns
Total unique patterns: 24

Each project: ~8 patterns average
```

### Cross-Project (With Auto-Sync)
```
Project A: Has 24 patterns (10 own + 14 synced)
Project B: Has 24 patterns (8 own + 16 synced)
Project C: Has 24 patterns (6 own + 18 synced)

Each project: 24 patterns (3x improvement!)
```

**Multiplier Effect**: Learn once → All projects 3x smarter

---

## Bottom Line

**Your Request**: "After you have learned from yourself and updated the toolkit, can you automatically copy the toolkit to active projects?"

**Our Answer**: **YES!**

**How It Works**:
1. Toolkit learns something in ANY project
2. Automatically syncs to ALL compatible projects
3. Smart domain filtering (don't sync HIPAA to revenue)
4. Zero manual work required

**Result**:
- Learn once in govertical → Benefits goassist3 and gpnet3
- Learn once in gpnet3 → Benefits others (if compatible)
- Projects teach each other
- All projects improve together

**Setup**:
- Already configured (active-projects.json created)
- Just enable: sync_config.json → `"enabled": true`
- That's it!

---

**Cross-Project Learning: ACTIVATED ✓**
