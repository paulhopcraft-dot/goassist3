# Agent Chain Execution Engine

<overview>
The Agent Chain Engine orchestrates multiple specialist agents to work together, either sequentially or in parallel, to provide comprehensive analysis and validation.
</overview>

<chain_types>
## Sequential Chain
Agents execute one after another, each receiving output from previous:
```
Agent A → Output → Agent B → Output → Agent C
```

**Use cases**:
- Test generation → Coverage analysis → Quality review
- PRD check → Implementation → Verification
- Code review → Security scan → Performance analysis

## Parallel Chain
Agents execute simultaneously, results are merged:
```
Agent A ↘
Agent B → Merge → Final Output
Agent C ↗
```

**Use cases**:
- Multiple domain validations (healthcare + security + performance)
- Comprehensive verification (tests + code quality + compliance)
- Independent analyses that don't depend on each other

## Conditional Chain
Agents execute based on conditions:
```
if (domain === 'healthcare') → HealthcareValidator
else if (domain === 'finance') → FinanceValidator
else → GeneralValidator
```

**Use cases**:
- Domain-specific validation (only in regulated projects)
- Optional agents (only if security-sensitive code)
- Context-aware processing (different agents for different file types)
</chain_types>

<execution_protocol>
<step number="1">
**Load Chain Definition**
- Read `.claude/agents/registry.json`
- Identify chain by name (e.g., "full-verification")
- Parse chain steps and conditions
</step>

<step number="2">
**Resolve Agent Definitions**
- For each agent in chain, load definition from `agents/definitions/*.md`
- Verify agent is enabled in current project (check domain.json)
- Check if agent is allowed in current context
</step>

<step number="3">
**Execute Chain**
**Sequential**:
```
for each step in chain:
    execute_agent(step.agent)
    collect_output()
    pass to next agent as context
```

**Parallel**:
```
agents = [spawn_agent(step.agent) for step in chain]
results = await_all(agents)
merged = merge_results(results)
```

**Conditional**:
```
for each step in chain:
    if evaluate_condition(step.if):
        execute_agent(step.agent)
        collect_output()
```
</step>

<step number="4">
**Merge Outputs**
- Combine all agent reports
- Deduplicate findings
- Prioritize critical issues
- Generate unified report
</step>

<step number="5">
**Update Project State**
- Add agent results to features.json (optional metadata)
- Create/update compliance reports
- Block or warn based on severity
- Log execution for analytics
</step>
</execution_protocol>

<example_usage>
## Full Verification Chain Example

**User runs**: `/verify`

**Chain loads**: "full-verification" from registry.json

**Execution**:
```
Step 1: test-specialist (Sequential)
→ Analyzes test coverage
→ Identifies untested paths
→ Suggests additional tests
→ Output: Coverage report

Step 2: code-reviewer (Sequential, receives coverage report)
→ Reviews code quality
→ Checks security (OWASP Top 10)
→ Analyzes performance
→ Output: Code review report

Step 3: healthcare-validator (Conditional: only if domain === 'healthcare')
→ Scans for PHI exposure
→ Validates HIPAA compliance
→ Checks evidence chain
→ Output: Compliance report

Step 4: Merge Results
→ Combine all reports
→ Priority: CRITICAL > HIGH > MEDIUM > LOW
→ Show unified verification status
```

**Output to user**:
```
## Verification Report

### Test Coverage (test-specialist)
✓ Line coverage: 87%
✗ Missing tests for error recovery path
⚠ Edge case: null input not tested

### Code Quality (code-reviewer)
✓ No security vulnerabilities
✗ Function complexity too high (line 42: 15 branches)
⚠ N+1 query detected (line 78)

### Healthcare Compliance (healthcare-validator)
✓ No PHI in logs
✓ Encryption configured correctly
✗ Evidence chain missing reason codes

### Summary
- CRITICAL: 1 (Fix evidence chain)
- HIGH: 2 (Function complexity, N+1 query)
- MEDIUM: 2 (Edge cases, test coverage)
- BLOCKING: YES (cannot merge until critical fixed)
```
</example_usage>

<agent_communication>
## Context Passing Between Agents

Agents can share context in sequential chains:

**Example**: test-specialist → code-reviewer
```
test-specialist output:
{
  "coverage": {
    "untested_functions": ["processPayment", "refundTransaction"]
  }
}

code-reviewer receives context:
"Focus review on untested functions: processPayment, refundTransaction"

code-reviewer output:
{
  "untested_security_risk": "processPayment handles money without tests - HIGH RISK"
}
```

This enables agents to build on each other's findings.
</agent_communication>

<configuration>
## Registry Configuration

Define chains in `.claude/agents/registry.json`:

```json
{
  "chains": {
    "full-verification": {
      "description": "Complete feature verification",
      "steps": [
        {"agent": "test-specialist", "phase": "test-validation"},
        {"agent": "code-reviewer", "phase": "quality-check"},
        {"agent": "healthcare-validator", "phase": "compliance", "if": "domain === 'healthcare'"}
      ]
    },
    "quick-review": {
      "description": "Fast code review without compliance",
      "steps": [
        {"agent": "code-reviewer", "phase": "security-and-quality"}
      ]
    },
    "compliance-only": {
      "description": "Only domain compliance, no code review",
      "steps": [
        {"agent": "healthcare-validator", "phase": "compliance", "if": "domain === 'healthcare'"},
        {"agent": "finance-validator", "phase": "compliance", "if": "domain === 'finance'"}
      ]
    }
  }
}
```

## Project Configuration

Enable/disable agents per project in `.claude/domain.json`:

```json
{
  "domain": "healthcare",
  "agents": {
    "enabled": ["healthcare-validator", "test-specialist", "code-reviewer"],
    "auto_trigger": {
      "healthcare-validator": ["prd-check", "build-prd", "verify"],
      "test-specialist": ["tdd", "verify"],
      "code-reviewer": ["review", "verify"]
    }
  }
}
```
</configuration>

<error_handling>
## Agent Failure Handling

If an agent fails during chain execution:

1. **Sequential**: Stop chain, report failure, return partial results
2. **Parallel**: Continue other agents, mark failed agent, return partial results
3. **Conditional**: If condition fails, skip agent gracefully

**Example**:
```
Chain: test-specialist → code-reviewer → healthcare-validator

If code-reviewer fails:
- test-specialist results: ✓ Available
- code-reviewer results: ✗ FAILED (timeout after 60s)
- healthcare-validator: ⊘ Skipped (dependency failed)

User sees:
"Verification incomplete: code-reviewer timed out. Test results available.
Re-run /verify to retry."
```
</error_handling>

<extensibility>
## Adding New Agents

To add a custom agent:

1. Create agent definition: `agents/definitions/my-agent.md`
2. Register in `agents/registry.json`
3. Add to chain or create new chain
4. Enable in project's `domain.json`

**Example - Adding Security Scanner**:

```markdown
<!-- agents/definitions/security-scanner.md -->
---
name: security-scanner
domain: security
version: 1.0.0
---

<agent_role>
You are a security expert specializing in vulnerability detection.
</agent_role>

<capabilities>
- OWASP Top 10 vulnerability detection
- Dependency vulnerability scanning
- Secret detection in code
- Authentication/authorization review
</capabilities>

<workflow>
<step number="1">
**Scan Dependencies**
Run npm audit / pip-audit / go mod verify
</step>

<step number="2">
**Check for Secrets**
Search for hardcoded API keys, passwords, tokens
</step>

<step number="3">
**Review Auth Logic**
Verify authentication/authorization implementation
</step>

<step number="4">
**Report Vulnerabilities**
List all security issues with severity and remediation
</step>
</workflow>
```

Then register:
```json
{
  "agents": {
    "security-scanner": {
      "file": "security-scanner.md",
      "domain": "security",
      "triggers": ["review", "verify", "security-scan"],
      "capabilities": ["vulnerability-detection", "secret-scanning"],
      "enabled_for": ["all"]
    }
  }
}
```

And add to chain:
```json
{
  "chains": {
    "security-verification": {
      "description": "Security-focused verification",
      "steps": [
        {"agent": "security-scanner", "phase": "vulnerability-scan"},
        {"agent": "code-reviewer", "phase": "secure-coding-review"}
      ]
    }
  }
}
```
</extensibility>

<integration>
## Command Integration

Commands trigger agents via agent registry:

**/verify** command:
```xml
<agent_integration>
<trigger_chain>full-verification</trigger_chain>
<fallback>If agent system disabled, run basic verification</fallback>
</agent_integration>
```

**/review** command:
```xml
<agent_integration>
<trigger_agents>code-reviewer</trigger_agents>
<mode>single</mode>
</agent_integration>
```

**/prd-check** (healthcare project):
```xml
<agent_integration>
<trigger_agents>healthcare-validator</trigger_agents>
<condition>domain === 'healthcare'</condition>
</agent_integration>
```
</integration>
