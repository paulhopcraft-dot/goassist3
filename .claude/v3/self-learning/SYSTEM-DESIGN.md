# v3.1: Self-Learning Toolkit System Design

## Vision: "Set It and Forget It"

**User Goal**: Don't learn the toolkit - let the toolkit learn YOU

**System Goal**: Observe usage → Detect patterns → Update itself → Get better over time

---

## Architecture: The Learning Loop

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERACTION                        │
│  User runs: /build-prd "payment processing"                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  1. EXECUTION TRACKING                      │
│  - Log command used                                         │
│  - Log parameters                                           │
│  - Log context (domain, features, time)                     │
│  - Assign execution ID                                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  2. OUTCOME DETECTION                       │
│  - Did tests pass? ✓/✗                                     │
│  - Did build succeed? ✓/✗                                  │
│  - Did code review find issues? ✓/✗                        │
│  - User satisfaction (implicit: did they retry? undo?)      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  3. PATTERN MINING                          │
│  - Analyze last 20 executions                               │
│  - Detect: What leads to success?                           │
│  - Detect: What leads to failure?                           │
│  - Detect: What patterns repeat?                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  4. AUTO-IMPROVEMENT                        │
│  IF pattern detected:                                       │
│    - Generate improved prompt/skill/command                 │
│    - A/B test: old vs new                                   │
│    - If new is better: UPDATE and COMMIT                    │
│    - If new is worse: ROLLBACK                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  5. FEEDBACK TO USER                        │
│  "💡 Toolkit learned: SOX audit logging now checked first" │
│  "🎯 Created /build-payment from your 5 payment features"  │
│  "⚡ Updated code-reviewer: auto-detects your SQL patterns" │
└─────────────────────────────────────────────────────────────┘
```

---

## Component 1: Execution Tracking

**File**: `.claude/v3/self-learning/execution-log.jsonl`

Every command execution is logged:

```jsonl
{"id": "exec_001", "timestamp": "2025-12-25T10:00:00Z", "command": "/build-prd", "params": {"feature": "payment processing", "prd_section": "8"}, "domain": "revenue", "user": "user_id", "context": {"similar_features": ["F007"], "compliance": ["SOX", "GAAP"]}}
{"id": "exec_002", "timestamp": "2025-12-25T10:15:00Z", "command": "/verify", "params": {}, "domain": "revenue", "related_to": "exec_001"}
```

**Captured Data**:
- Command used
- Parameters
- Domain context
- Time of day (are you more successful in mornings?)
- Related executions (build → verify → commit chain)

---

## Component 2: Outcome Detection

**File**: `.claude/v3/self-learning/outcomes.jsonl`

Link outcomes to executions:

```jsonl
{"exec_id": "exec_001", "outcome": "success", "evidence": {"tests_passed": true, "build_succeeded": true, "code_review_issues": 0, "user_action": "committed"}, "quality_score": 95}
{"exec_id": "exec_003", "outcome": "failure", "evidence": {"tests_passed": false, "build_succeeded": false, "error": "Missing audit logging"}, "quality_score": 30}
```

**Detection Methods**:

1. **Explicit Outcome** (Best):
   - Tests pass/fail
   - Build succeeds/fails
   - Code review finds issues

2. **Implicit Outcome** (Good):
   - User commits = success
   - User runs `/undo` = failure
   - User re-runs same command = likely failure first time

3. **User Feedback** (Optional):
   - Prompt: "Did this work well? 👍 👎"
   - Track: User manually marks outcomes

---

## Component 3: Pattern Mining

**File**: `.claude/v3/self-learning/pattern-analyzer.md`

Analyze execution logs to find patterns:

### **Pattern Type 1: Repeated Failures**

```
Analysis of last 20 executions:
- /build-prd run 8 times
- 3 times: Missing audit logging (SOX violation)
- Pattern: When building financial features, 37.5% forget audit logging

LEARNING: Add "Check audit logging FIRST" to /build-prd template
```

### **Pattern Type 2: Repeated Commands**

```
Analysis of last 30 days:
- User built 7 payment-related features
- All use: Stripe SDK, Decimal type, webhook validation
- Pattern: User specializes in payment systems

LEARNING: Create /build-payment specialized command
LEARNING: Create payment-expert skill with user's patterns
```

### **Pattern Type 3: Successful vs Failed Approaches**

```
Analysis: /verify command
- When run AFTER /tdd: 90% success rate
- When run WITHOUT /tdd: 50% success rate
- Pattern: TDD leads to better verification outcomes

LEARNING: Update /build-prd to recommend /tdd first
LEARNING: Create auto-chain: /build-prd → /tdd → /verify
```

### **Pattern Type 4: Time-Based Patterns**

```
Analysis: User success rate by time
- Morning (8-11am): 85% success
- Afternoon (2-5pm): 70% success
- Evening (8-11pm): 55% success

LEARNING: In evening, increase validation strictness (more prone to errors)
LEARNING: Suggest breaks if error rate increases
```

---

## Component 4: Auto-Improvement Engine

**File**: `.claude/v3/self-learning/auto-improver.md`

### **Improvement Workflow**:

```markdown
STEP 1: Detect Pattern (from Component 3)
Pattern: "Audit logging missed 3/8 times (37.5%)"

STEP 2: Generate Improved Version
Use meta-prompting:
"Current /build-prd template has 37.5% failure rate on audit logging.
Generate improved version that checks audit logging FIRST."

Generated Improvement:
```diff
<workflow>
+STEP 0: Domain Compliance Check
+- Read domain.json
+- IF audit_trail = "required":
+    Add to EVERY step: "Log with auditLog.record(...)"
+
STEP 1: Design Feature
...
```

STEP 3: A/B Test
- Version A: Old template (baseline: 37.5% failure)
- Version B: New template (test with next 5 executions)

STEP 4: Measure Results
After 5 executions with Version B:
- Success rate: 100% (5/5)
- No audit logging missed

STEP 5: Promote or Rollback
IF Version B > Version A:
  - Update /build-prd template
  - Commit: "auto: improve /build-prd - add audit logging check (0% → 100%)"
  - Notify user: "💡 Toolkit learned to check audit logging first"
ELSE:
  - Rollback to Version A
  - Log: Why did it fail?
```

---

## Component 5: Auto-Generated Specializations

### **Example 1: Command Specialization**

**Detected Pattern**:
```
User built 7 payment features:
- F007: Stripe integration
- F010: Invoice processing
- F012: Refund handling
- F015: Subscription billing
- F018: Payment webhooks
- F020: Fraud detection
- F023: Chargeback management

Common patterns:
- All use Decimal type
- All use Stripe SDK
- All have webhook validation
- All have audit logging
- All have idempotency keys
```

**Auto-Generated Command**:
```markdown
File: .claude/commands/build-payment.md

# /build-payment Command
# Auto-generated: 2025-12-25
# Based on: 7 successful payment features by user
# Success rate: 95% (user's payment features)

<command_role>
Build payment processing features following YOUR established patterns
</command_role>

<user_patterns_learned>
From your previous payment features:
- You always use Stripe SDK (from F007, F010, F012, F015, F018, F020, F023)
- You always use Decimal for money (GAAP requirement)
- You always validate webhooks (learned from F018 security issue)
- You always use idempotency keys (learned from F012 duplicate charge bug)
- You always log to auditLog (SOX requirement)
</user_patterns_learned>

<workflow>
STEP 0: Load YOUR Payment Patterns
- Read: F007, F010, F012, F015, F018, F020, F023
- Copy: Stripe configuration, webhook validation, error handling

STEP 1: Implement Payment Feature
- Use Decimal type (you ALWAYS do this)
- Use Stripe SDK (you ALWAYS do this)
- Add idempotency key parameter (you learned this from F012)
- Validate webhook signature (you learned this from F018)
- Log all mutations (you ALWAYS do this)

STEP 2: Security Checks
- Verify: Webhook signature validation included
- Verify: Idempotency prevents duplicate charges
- Verify: No sensitive data in logs

STEP 3: Test with YOUR patterns
- Test: Idempotency (duplicate requests rejected)
- Test: Webhook signature (invalid rejected)
- Test: Decimal precision (no rounding errors)
- Coverage: 80%+ (your quality gate)
</workflow>

<why_this_works>
This command was generated by analyzing YOUR 7 successful payment features.
It follows YOUR patterns, not generic best practices.
Success rate: 95% (based on your history)
</why_this_works>
```

**User Experience**:
```
User: /build-payment "subscription billing"
Claude: "Using your payment patterns from F007, F010, F012...
         [Builds feature following user's exact patterns]
         ✓ Stripe SDK configured
         ✓ Decimal precision
         ✓ Webhook validation (learned from F018)
         ✓ Idempotency (learned from F012)
         ✓ Audit logging"

Result: Feature works first try, no forgotten patterns
```

---

### **Example 2: Skill Specialization**

**Detected Pattern**:
```
User works in healthcare domain (gpnet3):
- 15 features built, all HIPAA-compliant
- 0 PHI leaks in production
- Common patterns: Encryption, audit trails, BAAs
```

**Auto-Generated Skill**:
```markdown
File: .claude/skills/user-healthcare-expert/SKILL.md

# Your Healthcare Expertise (Auto-Generated)

<learned_from_user>
Based on your 15 HIPAA-compliant features:

YOUR HIPAA PATTERNS:
- Always encrypt PHI at rest (AES-256)
- Always use TLS 1.3 for transmission
- Always log PHI access (who, what, when, why)
- Always check BAAs before third-party integration
- Never log PHI in console.log (you learned this early)

YOUR CODE PATTERNS:
- PHI fields: Always use encrypted_field() wrapper
- API responses: Always use sanitize() to remove PHI
- Database queries: Always use parameterized (no SQL injection)
- Error messages: Always generic (never leak patient info)

YOUR SECURITY CHECKS:
- Pre-commit: Grep for console.log with PHI patterns
- Pre-deploy: Verify encryption enabled
- Post-deploy: Audit log completeness check
</learned_from_user>

<auto_triggers>
This skill activates when:
- domain.json contains "healthcare" or "HIPAA"
- User builds features in gpnet3 project
- PHI-related code detected (patient, medical, diagnosis, etc.)
</auto_triggers>

<workflow>
On every /build-prd in healthcare:
1. Check: Is PHI involved?
2. Apply: YOUR encryption patterns
3. Apply: YOUR audit logging patterns
4. Verify: No console.log with PHI
5. Verify: BAA exists if third-party
6. Test: YOUR HIPAA test suite
</workflow>
```

---

## Component 6: Continuous Validation

**File**: `.claude/v3/self-learning/validation-engine.md`

Before deploying improvements, validate:

### **Validation Checklist**:

```markdown
BEFORE updating /build-prd template:

1. **A/B Test Results**:
   - Old version: 37.5% failure rate
   - New version: 0% failure rate (5/5 success)
   - Statistical significance: ✓ (enough samples)

2. **No Regressions**:
   - Run old test suite with new template
   - All tests still pass: ✓

3. **User Approval** (Optional):
   - Show diff to user
   - Ask: "Toolkit learned to check audit logging first. Apply? Y/n"
   - If no response in 24h: Auto-apply (user trusts toolkit)

4. **Rollback Plan**:
   - Old version saved: .claude/v3/self-learning/backups/build-prd-v1.md
   - Rollback command: /rollback build-prd
   - Auto-rollback if: Failure rate increases

5. **Commit Update**:
   - Message: "auto: improve /build-prd - add audit check (37.5% → 0% failure)"
   - Tag: learning-v1.1
   - Push to repo (if configured)
```

---

## User Experience Examples

### **Week 1: Toolkit Observes**

```
User builds 3 features normally
Toolkit: [Silently logs patterns, no changes yet]
```

### **Week 2: First Learning**

```
User builds 5th payment feature
Toolkit: "💡 I noticed you've built 5 payment features.
          Would you like me to create a /build-payment command
          with your patterns? It'll be faster next time."

User: "Yes"

Toolkit: [Creates /build-payment.md]
         "✓ Created /build-payment with your Stripe + Decimal patterns"
```

### **Week 3: Automatic Improvement**

```
User builds feature, forgets audit logging, tests fail
User fixes, commits

Toolkit: [Detects pattern: audit logging forgotten 2/7 times]
         [Generates improved /build-prd]
         [A/B tests with next 3 features]
         [Success rate: 100%]
         [Auto-updates command]

Toolkit: "💡 I updated /build-prd to check audit logging first.
          You haven't forgotten it since!"
```

### **Month 2: Fully Personalized**

```
Toolkit now has:
- /build-payment (your payment patterns)
- /build-api (your API patterns)
- payment-expert skill (your Stripe expertise)
- api-security skill (your auth patterns)
- Auto-audit-check (prevents your common mistakes)
- Auto-test-coverage (runs your preferred test suite)

Result: Toolkit feels like YOUR custom AI assistant
```

---

## Privacy & Control

### **User Controls**:

**Opt-in to learning**:
```json
{
  "self_learning": {
    "enabled": true,
    "auto_update": true,
    "ask_before_update": false,
    "share_learnings": false
  }
}
```

**Review learnings**:
```bash
/toolkit:learnings          # Show what toolkit learned
/toolkit:improvements       # Show proposed improvements
/toolkit:rollback           # Undo last auto-update
```

**Privacy**:
- All learning is LOCAL (your machine only)
- No data sent to external servers
- Git commits show all changes
- Full transparency

---

## Implementation Phases

### **Phase 1: Tracking** (Week 1)
- Add execution logging
- Add outcome detection
- No auto-updates yet (just observe)

### **Phase 2: Pattern Detection** (Week 2)
- Analyze logs for patterns
- Generate improvement suggestions
- Show to user for approval

### **Phase 3: A/B Testing** (Week 3)
- Test improvements before applying
- Measure success rates
- Rollback if worse

### **Phase 4: Full Automation** (Week 4)
- Auto-update with user approval
- Continuous learning loop
- Self-improving toolkit

---

## Success Metrics

**Track toolkit improvement over time**:

```json
{
  "week_1": {
    "feature_success_rate": 70,
    "test_pass_rate": 65,
    "code_review_issues": 12,
    "user_retries": 8
  },
  "week_4": {
    "feature_success_rate": 92,
    "test_pass_rate": 95,
    "code_review_issues": 2,
    "user_retries": 1
  },
  "improvement": {
    "success_rate": "+31%",
    "test_pass_rate": "+46%",
    "code_review_issues": "-83%",
    "user_retries": "-87%"
  }
}
```

**Goal**: Toolkit gets measurably better every week

---

## Why This is Revolutionary

### **Traditional Tools**:
- Static commands/features
- Generic for all users
- No learning from usage
- Manual updates required

### **This Self-Learning Toolkit**:
- ✅ Commands improve automatically
- ✅ Personalized to YOUR patterns
- ✅ Learns from YOUR mistakes
- ✅ Gets better the more you use it
- ✅ Zero manual configuration

### **The Compounding Effect**:

```
Week 1: 70% success rate (generic toolkit)
Week 2: 75% (learned your domain)
Week 4: 85% (learned your patterns)
Week 8: 92% (learned your mistakes)
Week 16: 97% (fully personalized)

After 6 months: Toolkit knows YOU better than you know yourself
```

---

## Next Steps

1. **Enable tracking** (opt-in)
2. **Run normally for 2 weeks** (toolkit observes)
3. **Review first learnings** (approve improvements)
4. **Enable auto-update** (set it and forget it)
5. **Watch toolkit get smarter** (every week)

---

**Bottom Line**:
You don't learn the toolkit - **the toolkit learns YOU**.

The more you use it, the better it gets at being YOUR personal AI assistant.
