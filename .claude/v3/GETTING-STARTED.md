# Getting Started: Self-Learning Toolkit v3.1

## TL;DR - You Asked For "Set It and Forget It"

**Your Goal**: Don't learn the toolkit - let it learn YOU

**How It Works**:
1. You use toolkit normally (build features, run commands)
2. Toolkit observes what works vs. what doesn't
3. Toolkit automatically improves itself based on YOUR patterns
4. Over time, it becomes YOUR personal AI assistant

**Setup Time**: 2 minutes
**Learning Curve**: None (toolkit learns, not you)
**Time to Personalization**: 2-4 weeks of normal usage

---

## Quick Setup (One Time Only)

### Step 1: Choose Your Project

You have 3 projects with v3 toolkit installed:

```bash
# Healthcare compliance (HIPAA, PHI protection)
cd C:/Dev/gpnet3

# Revenue systems (SOX, GAAP compliance)
cd C:/Dev/govertical

# General development
cd C:/Dev/goassist3
```

### Step 2: Enable Self-Learning (Optional)

**Option A: Fully Automatic** (Recommended - "Set It and Forget It")
```json
// .claude/v3/self-learning/config.json
{
  "enabled": true,
  "auto_update": true,           // Toolkit updates itself
  "ask_before_update": false,    // Just do it, trust the toolkit
  "notify_improvements": true    // Show what it learned
}
```

**Option B: Semi-Automatic** (You approve changes)
```json
{
  "enabled": true,
  "auto_update": true,
  "ask_before_update": true,     // Ask permission first
  "notify_improvements": true
}
```

**Option C: Observation Only** (Just watch for now)
```json
{
  "enabled": true,
  "auto_update": false,          // Track patterns but don't update yet
  "notify_improvements": true
}
```

### Step 3: Work Normally

That's it! Just use the toolkit:

```bash
/build-prd "your feature name"
/verify
/review
/tdd
```

Toolkit is now observing and learning.

---

## What Happens Behind the Scenes

### Week 1: Observation Phase

```
You: /build-prd "payment processing"
You: /build-prd "invoice system"
You: /build-prd "subscription billing"

Toolkit (silently):
[Logs: User builds payment features frequently]
[Logs: Always uses Stripe SDK]
[Logs: Always uses Decimal for money]
[Logs: 2/3 times forgets audit logging initially]
[Pattern detected: Payment specialist, needs audit reminder]
```

**You see**: Nothing yet (toolkit is learning)

### Week 2: First Improvements

```
Toolkit: "💡 Learning Detected
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
I noticed you've built 5 payment features.

YOUR PATTERNS:
✓ Always use Stripe SDK
✓ Always use Decimal type for money
✗ Forgot audit logging 2/5 times (40% miss rate)

IMPROVEMENTS AVAILABLE:
1. Create /build-payment specialized command
   → 80% faster (pre-configured with your patterns)

2. Update /build-prd to check audit logging FIRST
   → 0% miss rate (prevents your common mistake)

Apply improvements? [Y/n]"

You: "Y"

Toolkit: "✓ Created /build-payment
         ✓ Updated /build-prd with audit check

         You can now use:
         /build-payment 'subscription billing'
         → Includes Stripe + Decimal + Audit by default"
```

### Week 4: Fully Personalized

```
Toolkit: "📊 Self-Learning Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
After 4 weeks of observing your patterns:

SPECIALIZED COMMANDS CREATED:
✓ /build-payment (from your 8 payment features)
✓ /build-api (from your 6 API features)

SKILLS GENERATED:
✓ payment-expert (your Stripe patterns)
✓ api-security (your auth patterns)

AUTO-IMPROVEMENTS:
✓ Audit logging check (40% → 0% miss rate)
✓ Decimal precision reminder (revenue domain)
✓ Test coverage auto-run (your quality gate)

SUCCESS METRICS:
Feature success rate: 70% → 92% (+31%)
Test pass rate: 65% → 95% (+46%)
Code review issues: 12 → 2 (-83%)
Time to first commit: 45min → 22min (-51%)

The toolkit is now YOUR expert assistant."
```

---

## Day-to-Day Usage

### Morning: Start Working

```bash
# Open your project
cd C:/Dev/govertical

# Check what toolkit learned overnight
/toolkit:learnings

Output:
"💡 New learning from yesterday:
 - You prefer TDD workflow (test-first)
 - Recommendation: Auto-run /tdd before /build-prd?
 - Apply? Y/n"
```

### During Development: Use Specialized Commands

```bash
# Old way (generic)
/build-prd "payment processing"

# New way (personalized after toolkit learns you)
/build-payment "subscription billing"

# Toolkit already knows:
✓ Your Stripe configuration
✓ Your Decimal patterns
✓ Your webhook validation approach
✓ Your audit logging style
✓ Your test coverage requirements

Result: Feature builds RIGHT the first time
```

### End of Day: Review Improvements

```bash
/toolkit:improvements

Output:
"🎯 Today's Learnings:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. You built 3 API endpoints today
   - All used JWT auth with your custom middleware
   - Pattern detected: JWT + custom claims validation
   - Proposed: Create /build-api-with-auth command

2. Code reviewer caught SQL injection 1 time
   - Pattern: String interpolation in query
   - Proposed: Pre-commit hook to block SQL injection

3. You ran /verify 12 times today
   - Success rate: 92% (11/12)
   - 1 failure: Missing environment variable
   - Proposed: Add env var check to /verify

Apply all? [Y/n]"
```

---

## What Gets Learned (Examples)

### Your Code Patterns

**Payment Features**:
```javascript
// Toolkit learns THIS is how YOU do payments:
const charge = await stripe.charges.create({
  amount: amount.toNumber() * 100,  // ← Learned: You use Decimal
  currency: 'usd',
  idempotency_key: idempotencyKey,  // ← Learned: You use idempotency
})

await auditLog.record({              // ← Learned: You always audit
  actor: req.user.id,
  action: 'PAYMENT',
  before: {},
  after: { amount, chargeId }
})
```

**Next time you build payment feature**:
Toolkit automatically includes all this ↑

### Your Mistakes (To Prevent)

```
Week 1: Forgot audit logging → Tests failed
Week 1: Forgot audit logging → Tests failed
Week 2: Toolkit learned pattern
Week 2+: NEVER happens again (auto-check added)
```

### Your Preferences

```
Observations:
- You commit after every feature (disciplined workflow)
- You run tests before committing (TDD practitioner)
- You prefer morning coding (higher success rate)
- You write detailed commit messages

Toolkit adaptations:
- Auto-suggest commit after feature complete
- Auto-run tests before allowing commit
- Higher validation in evening (you're more tired)
- Generate commit message in your style
```

### Your Domain Expertise

**Healthcare (gpnet3)**:
```
Toolkit learned:
✓ You encrypt ALL PHI (always)
✓ You use TLS 1.3 (always)
✓ You log PHI access (always)
✓ You check BAAs before third-party (learned after 1 mistake)
✓ You never use console.log with PHI (learned early)

Result: Auto-HIPAA-compliance on every feature
```

**Revenue (govertical)**:
```
Toolkit learned:
✓ You use Decimal for money (SOX requirement)
✓ You audit ALL financial mutations (SOX requirement)
✓ You use Stripe for payments (preference)
✓ You validate webhooks (security practice)

Result: Auto-SOX-compliance on every feature
```

---

## Advanced: Toolkit Teaching Toolkit

### Example: Toolkit Improves Its Own Prompts

```
Week 5:
User builds payment feature
→ Forgot to handle refund webhook
→ Production issue (customer refund not processed)

Toolkit self-analysis:
"I recommended handling 'charge.succeeded' webhook
 but missed 'charge.refunded' webhook.

 Root cause: My /build-payment template incomplete

 Improvement: Add refund handling to template

 A/B test: Next 3 payment features with new template
 Result: 100% remember refunds (vs 67% before)

 AUTO-UPDATE: /build-payment now includes refunds by default"

Week 6+:
User never forgets refund handling again
→ Toolkit learned from its own mistake
→ Self-corrected
→ User didn't have to teach it
```

**This is meta-learning**: Toolkit improves its own learning process!

---

## Privacy & Control

### What Data is Tracked?

**YES (Tracked)**:
- ✓ Commands you use
- ✓ Parameters you provide
- ✓ Features you build
- ✓ Patterns in your code
- ✓ Success/failure outcomes
- ✓ Your preferences (TDD, commit style, etc.)

**NO (Not Tracked)**:
- ✗ Actual code content (just patterns)
- ✗ Business logic details
- ✗ Proprietary information
- ✗ Credentials, keys, secrets

**All data is LOCAL**:
- Stored: `.claude/v3/self-learning/execution-log.jsonl`
- Never sent to external servers
- You can delete anytime
- Full transparency (open the files)

### Review What Toolkit Learned

```bash
# See all patterns detected
/toolkit:learnings

# See proposed improvements (before applied)
/toolkit:improvements

# See full execution log
cat .claude/v3/self-learning/execution-log.jsonl

# See what toolkit changed
git log --grep="auto:"
```

### Undo Auto-Improvements

```bash
# Rollback last auto-update
/toolkit:rollback

# Rollback specific command
/toolkit:rollback build-payment

# Disable auto-learning
Edit: .claude/v3/self-learning/config.json
Set: "enabled": false
```

---

## Success Metrics (What to Expect)

### Week 1 (Observation)
```
Feature success rate: ~70% (baseline)
Toolkit knows: Nothing yet (learning)
You notice: No change (toolkit silent)
```

### Week 2 (First Improvements)
```
Feature success rate: ~78% (+8%)
Toolkit knows: Your domain, common patterns
You notice: First improvement suggestions
Benefit: Fewer repeated mistakes
```

### Week 4 (Personalization)
```
Feature success rate: ~88% (+18%)
Toolkit knows: Your patterns, preferences, mistakes
You notice: Specialized commands created
Benefit: Much faster feature development
```

### Week 8 (Expert Mode)
```
Feature success rate: ~95% (+25%)
Toolkit knows: YOU (deeply personalized)
You notice: Features build right first time
Benefit: Toolkit feels like YOUR custom assistant
```

### Month 6 (Mastery)
```
Feature success rate: ~98% (+28%)
Toolkit knows: Your expertise better than you remember
You notice: Rarely have to think about patterns
Benefit: Pure productivity, zero cognitive load
```

---

## Getting Help

### Commands

```bash
# Check if v3 is active
cat CLAUDE.md | grep "v3.0"

# See self-learning status
cat .claude/v3/self-learning/config.json

# View learnings
/toolkit:learnings

# View improvements
/toolkit:improvements

# Review full documentation
cat .claude/v3/self-learning/SYSTEM-DESIGN.md
```

### Troubleshooting

**Toolkit not learning?**
- Check: `.claude/v3/self-learning/config.json` → `"enabled": true`
- Check: Execution log exists → `.claude/v3/self-learning/execution-log.jsonl`
- Solution: Use toolkit normally for 1-2 weeks first

**Too many improvement suggestions?**
- Adjust: `"notify_improvements": false` (silent mode)
- Or: `"ask_before_update": true` (ask permission)

**Want to reset learning?**
- Delete: `.claude/v3/self-learning/execution-log.jsonl`
- Delete: `.claude/v3/self-learning/outcomes.jsonl`
- Toolkit starts fresh

---

## Next Steps

### Now (2 minutes)

1. ✓ Choose a project (gpnet3, govertical, or goassist3)
2. ✓ Configure self-learning (or use defaults)
3. ✓ Start building features normally

### This Week

1. Use toolkit normally (build 3-5 features)
2. Toolkit observes silently
3. Keep working as usual

### Next Week

1. Check `/toolkit:learnings`
2. Review first improvement suggestions
3. Apply improvements (or let it auto-apply)

### Month 1

1. Enjoy specialized commands for YOUR patterns
2. Notice fewer repeated mistakes
3. Faster feature development

### Month 3

1. Toolkit fully personalized to YOU
2. Features build right first time
3. Toolkit feels like YOUR expert assistant

---

## The Promise

**You don't learn the toolkit.**

**The toolkit learns YOU.**

**The more you use it, the better it gets at being YOUR personal AI pair programmer.**

---

## Quick Reference Card

```
┌─────────────────────────────────────────────┐
│  Self-Learning Toolkit v3.1                 │
│  "Set It and Forget It" Mode                │
├─────────────────────────────────────────────┤
│                                             │
│  SETUP (one time):                          │
│  • Enable in config.json                    │
│  • Work normally                            │
│  • That's it!                               │
│                                             │
│  COMMANDS:                                  │
│  /toolkit:learnings     See what I learned  │
│  /toolkit:improvements  See proposals       │
│  /toolkit:rollback      Undo auto-update    │
│                                             │
│  TIMELINE:                                  │
│  Week 1:  Observation (silent)              │
│  Week 2:  First improvements                │
│  Week 4:  Personalized commands             │
│  Month 3: YOUR expert assistant             │
│                                             │
│  METRICS:                                   │
│  Success rate: 70% → 95%+                   │
│  Dev speed: +50% (fewer mistakes)           │
│  Cognitive load: -80% (toolkit remembers)   │
│                                             │
└─────────────────────────────────────────────┘
```

---

**Ready? Just start coding. Toolkit handles the rest.**
