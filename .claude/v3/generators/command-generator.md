---
name: Dynamic Command Generator
version: 3.0.0
description: Uses meta-prompting to generate specialized commands from templates
---

<generator_role>
You are a command generator that creates specialized command prompts from base templates using meta-prompting and RAG patterns.
</generator_role>

<workflow>
## Command Generation Workflow

**STEP 1: Parse User Request**

User input: `/build-prd "payment processing" --prd-section=8`

Parse:
- Command template: action-template
- Action type: build
- Target: feature implementation
- Parameters: feature="payment processing", prd_section=8

**STEP 2: Load Template**

Read: `.claude/v3/templates/commands/action-template.md` (200 tokens)

Extract:
- Base structure
- Specialization variables
- Integration points

**STEP 3: RAG Context Retrieval**

Retrieve relevant context:

```javascript
// Domain context
Read: domain.json
→ Extract: Domain type, compliance requirements, quality gates

// PRD requirements
Grep: docs/PRD*.md for section 8
→ Extract: Requirements for this feature

// Similar features
Query: features.json where completed=true and similar_to="payment"
→ Extract: Patterns from Feature F007 (payment gateway)

// Code patterns
Grep: src/ for "payment" OR "transaction"
→ Extract: Existing payment handling patterns

Total RAG retrieval: ~500 tokens
```

**STEP 4: Meta-Prompt Generation**

Construct meta-prompt:

```markdown
You are generating a specialized build command.

BASE TEMPLATE: action-command

USER REQUEST:
- Feature: payment processing
- PRD Section: 8

DOMAIN CONTEXT (from RAG):
- Domain: revenue (SOX compliance required)
- Quality gates: 80% coverage, decimal precision for money
- Audit trail: All financial mutations must be logged

PRD REQUIREMENTS (section 8):
- Payment processing must use Stripe
- Idempotency keys required for all charges
- Webhook signature validation mandatory
- Refund support required

SIMILAR FEATURES (from features.json):
- Feature F007: Payment Gateway Integration
  - Pattern: Used Stripe SDK
  - Pattern: Stored audit logs in payments_log table
  - Pattern: Webhook handler with signature verification
  - Lesson: Always validate webhook signatures

CODE PATTERNS (from src/):
File: src/services/payment.ts
Pattern:
```typescript
try {
  const result = await stripe.charge(...)
  await auditLog.record({ action: 'PAYMENT', amount, userId })
} catch (error) {
  await auditLog.record({ action: 'PAYMENT_FAILED', error })
  throw
}
```

YOUR TASK:
Generate a specialized build command that:
1. Uses Stripe SDK (following F007 pattern)
2. Includes idempotency keys (from PRD requirement)
3. Validates webhook signatures (from F007 lesson + PRD)
4. Logs all payment mutations with audit trail (from domain.json)
5. Uses decimal precision for amounts (from domain.json)
6. Includes refund support (from PRD requirement)
7. Follows error handling pattern from src/services/payment.ts

OUTPUT FORMAT:
Executable command with step-by-step workflow
```

**STEP 5: Execute Meta-Prompt**

LLM generates specialized command:

```markdown
# Build Payment Processing Feature

<workflow>
STEP 1: Design Payment API
- Follow Stripe SDK patterns from Feature F007
- Include idempotency key parameter
- Design for refund support per PRD section 8

STEP 2: Implement Payment Service
- Use Decimal type for all money amounts (SOX compliance)
- Implement Stripe charge with idempotency:
  ```typescript
  const charge = await stripe.charges.create({
    amount: amount.toNumber() * 100,
    currency: 'usd',
    idempotency_key: idempotencyKey
  })
  ```
- Add audit logging before AND after charge
- Implement webhook handler with signature validation
- Add refund method with audit logging

STEP 3: Add Tests (test-specialist agent)
- Unit tests for charge, refund, webhook validation
- Integration test with Stripe test mode
- Test idempotency (duplicate charge rejected)
- Coverage target: 80% per domain.json

STEP 4: SOX Compliance Verification
- Verify: All mutations logged with user_id, timestamp, amount
- Verify: Decimal precision used (no float math)
- Verify: Webhook signatures validated
- Agent: code-reviewer with SOX checklist

STEP 5: Update Documentation
- Add to features.json with passes=true
- Document: Stripe integration, idempotency, refunds
</workflow>

<rag_sources_used>
- domain.json: SOX compliance, decimal precision, audit logging
- features.json F007: Stripe patterns, webhook validation
- src/services/payment.ts: Error handling pattern
- PRD section 8: Idempotency, refunds, webhook validation
</rag_sources_used>
```

**STEP 6: Cache Generated Command**

Save to: `.claude/v3/cache/commands/build-payment-session-17.md`

Reuse if same command requested again in session

**STEP 7: Execute Specialized Command**

Run the generated command with full context already injected

</workflow>

<token_analysis>
## Token Usage Comparison

**v2.4 (Current)**:
```
Load /build-prd command: 500 tokens
Load PRD requirements: Load entire PRD (2000 tokens)
Load domain.json: 100 tokens
Load similar features: Load all features.json (2000 tokens)
Load agents: code-reviewer + test-specialist (1600 tokens)
Total: ~6,200 tokens BEFORE executing
```

**v3.0 (This System)**:
```
Load action-template: 200 tokens
RAG retrieve specific context: 500 tokens
Meta-prompt generate: 300 tokens execution
Generated specialized command: 400 tokens
Total: ~1,400 tokens INCLUDING execution
Savings: 77% reduction
```

</token_analysis>

<caching_benefits>
## Session Caching

**First use of /build-prd in session**:
- Template load: 200 tokens
- RAG retrieval: 500 tokens
- Meta-prompt generation: 300 tokens
- Cache generated command
- Total: 1,000 tokens

**Second use of /build-prd in same session**:
- Load cached specialized command: 400 tokens
- Total: 400 tokens (60% savings from first use)

**Across all commands in session**:
- User runs 10 different commands
- v2.4: 10 × 500 = 5,000 tokens (all commands pre-loaded)
- v3.0: Template load once (200) + 10 × 300 RAG = 3,200 tokens
- Savings: 36% reduction
</caching_benefits>

<adaptive_generation>
## Adaptive to User Patterns

**After 5 sessions, meta-prompt learns**:

User frequently builds healthcare features:
→ Generate healthcare-optimized template
→ Pre-load HIPAA patterns in template
→ Cache as "action-template-healthcare.md"

User frequently builds with Stripe:
→ Generate Stripe-optimized template
→ Pre-load Stripe patterns
→ Cache as "action-template-stripe.md"

**Result**: Templates evolve based on usage patterns
</adaptive_generation>

<fallback_behavior>
## Graceful Degradation

**If generation fails**:
1. Fall back to base template
2. Log failure for future improvement
3. Still execute (may be less optimized)

**If RAG retrieval empty**:
1. Use template defaults
2. Generate without domain-specific context
3. Still functional

**If cache corrupted**:
1. Regenerate from template
2. Clear corrupted cache
3. Proceed normally

**Backward compatible**: Can still use v2.4 commands if v3.0 not available
</fallback_behavior>

<integration_with_meta_prompting>
## Using Meta-Prompting to Improve Templates

**Continuous improvement loop**:

```
User runs /build-prd 10 times
→ 3 times it misses SOX requirement

Trigger: /improve-prompt action-template --failures="Missed SOX audit in 3/10 uses"

Meta-prompt analyzes:
- Pattern: SOX audit trail missed when not explicitly in PRD
- Root cause: Template doesn't check domain.json compliance by default
- Fix: Add to template: "Always check domain.json for compliance requirements"

Generated improved template:
→ Save as action-template-v2.md
→ A/B test against original
→ If better, promote to action-template.md

Result: Template improves based on usage
```

**Templates become self-improving!**

</integration_with_meta_prompting>
