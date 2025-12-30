---
description: Define constraints before implementing complex features
---

# Constraint Analysis: $ARGUMENTS

Define implementation boundaries BEFORE writing code:

## HARD CONSTRAINTS (Cannot Violate)

### Performance
- Response time: [e.g., <300ms p95]
- Throughput: [e.g., 100 req/sec]
- Latency budget: [component breakdown]

### Resource Limits
- Memory: [e.g., <2GB VRAM, <500MB RAM]
- CPU: [e.g., <70% sustained utilization]
- Storage: [e.g., <100MB on disk]
- Network: [e.g., <5MB download size]

### Security
- Authentication: [required methods]
- Authorization: [access control rules]
- Data handling: [encryption, PII rules]
- Compliance: [GDPR, HIPAA, etc.]

### Compatibility
- Must work with: [existing systems, APIs, versions]
- Cannot break: [specific integrations]
- Backward compatibility: [requirements]

### Business Rules
- Cost ceiling: [max $/month, $/request]
- SLA requirements: [uptime, recovery time]
- Legal requirements: [licenses, terms]

## SOFT PREFERENCES (Optimize For)

Rank by priority (1 = highest):
1. [e.g., Code simplicity]
2. [e.g., Maintainability]
3. [e.g., Test coverage >80%]
4. [e.g., Minimal dependencies]
5. [e.g., Observable/debuggable]

## ANTI-PATTERNS (Explicitly Avoid)

**Do NOT:**
- [e.g., Use global state]
- [e.g., Create N+1 query patterns]
- [e.g., Add dependencies >10MB]
- [e.g., Write untestable code]
- [e.g., Over-engineer with abstractions]

**Why these are forbidden:**
- [Reasoning for each anti-pattern]

## Constraint Validation

Before marking feature complete, verify:
- [ ] All hard constraints tested and passing
- [ ] Soft preferences optimized (at least top 3)
- [ ] No anti-patterns present in code
- [ ] Performance benchmarks meet targets
- [ ] Resource usage within limits

## Implementation Notes

Update features.json with constraints:
```json
{
  "id": "F00X",
  "constraints": {
    "hard": ["<300ms latency", "<2GB VRAM"],
    "soft": ["simple code", "high test coverage"],
    "anti_patterns": ["no global state", "no N+1 queries"]
  },
  "validation": {
    "performance_test": "test_latency.py",
    "resource_test": "test_vram_usage.py"
  }
}
```

Now implement within these boundaries.
