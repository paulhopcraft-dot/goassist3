---
description: Role-Based Constraint Prompting - Get 10x more specific outputs
---

<instructions>
Assign expert roles with specific constraints for dramatically better outputs.

Use this when you need production-quality code, not generic examples.

**Task:** $ARGUMENTS
</instructions>

<workflow>
<step number="1">
<title>Define the Expert Role</title>
<define>
Based on the task, determine:

**Expert Role:**
- Title: [e.g., "Senior Python Engineer", "DevOps Architect", "ML Engineer"]
- Experience: [e.g., "10 years", "15 years"]
- Domain: [e.g., "data pipeline optimization", "distributed systems", "computer vision"]
- Specialization: [e.g., "real-time processing", "cloud infrastructure", "production ML"]
</define>

<example>
```
You are a Senior Python Engineer with 10 years experience in data pipeline
optimization, specializing in real-time processing at scale.
```
</example>
</step>

<step number="2">
<title>Extract/Define Constraints</title>
<identify>Identify or ask for **3-5 specific technical constraints**</identify>

<constraint_categories>
<category name="Technology Stack">
- Must use: [specific libraries/frameworks]
- Cannot use: [prohibited tools]
- Version requirements: [e.g., Python 3.11+, Node 18+]
</category>

<category name="Performance">
- Latency: [e.g., sub-100ms, <500ms p95]
- Throughput: [e.g., 10M records/hour, 1000 req/sec]
- Memory: [e.g., max 2GB footprint, <500MB RAM]
- CPU: [e.g., <30% utilization, single-threaded]
</category>

<category name="Reliability">
- Availability: [e.g., 99.9% uptime, zero downtime]
- Data integrity: [e.g., zero data loss, exactly-once delivery]
- Error handling: [e.g., graceful degradation, retry logic]
</category>

<category name="Code Quality">
- Test coverage: [e.g., >80%, all critical paths]
- Documentation: [e.g., inline, docstrings, type hints]
- Style: [e.g., follows PEP8, linted, formatted]
</category>

<category name="Deployment">
- Environment: [e.g., Docker, Kubernetes, serverless]
- Monitoring: [e.g., Prometheus metrics, structured logging]
- Configuration: [e.g., 12-factor, env vars]
</category>

<category name="Security">
- Authentication: [e.g., OAuth2, API keys]
- Data handling: [e.g., encrypt at rest, no PII in logs]
- Dependencies: [e.g., no CVEs, pinned versions]
</category>
</constraint_categories>

<clarification>
If constraints aren't obvious from the task, ask:
"What are the critical constraints for this implementation?"
</clarification>
</step>

<step number="3">
<title>Define Output Format</title>
<deliverables>
Specify exactly what format you need:

**Code Deliverables:**
- [ ] Production-ready code (not prototype)
- [ ] Inline documentation
- [ ] Type hints/annotations
- [ ] Error handling
- [ ] Logging
- [ ] Configuration
- [ ] Unit tests
- [ ] Integration tests
- [ ] README with usage examples

**Documentation:**
- [ ] Architecture diagram (mermaid)
- [ ] API documentation
- [ ] Deployment instructions
- [ ] Performance characteristics
- [ ] Trade-offs explained
</deliverables>

<note>Select what's needed for this task.</note>
</step>

<step number="4">
<title>Construct the Expert Prompt</title>
<template>
```
========================================
EXPERT ROLE
========================================

You are a [Role] with [X years] experience in [Domain],
specializing in [Specialization].

Your task: [Specific task description]

========================================
CONSTRAINTS
========================================

Technology Stack:
- [Constraint 1]
- [Constraint 2]

Performance:
- [Constraint 3]

Reliability:
- [Constraint 4]

Code Quality:
- [Constraint 5]

[Add more categories as needed]

========================================
OUTPUT FORMAT
========================================

Deliver:
1. [Deliverable 1 - e.g., Production-ready Python code]
2. [Deliverable 2 - e.g., Unit tests with >80% coverage]
3. [Deliverable 3 - e.g., README with deployment guide]
4. [Deliverable 4 - e.g., Performance benchmarks]

Code Requirements:
- Inline documentation for complex logic
- Type hints for all functions
- Error handling with specific exceptions
- Structured logging (JSON format)
- Configuration via environment variables

========================================
```
</template>
</step>

<step number="5">
<title>Execute as Expert</title>
<implement>
Now implement the task **strictly adhering to the role and constraints**.
</implement>

<execution_rules>
1. **Stay in character** - Think like the expert you defined
2. **Honor ALL constraints** - No shortcuts or "good enough"
3. **Match output format exactly** - Deliver what was specified
4. **Explain trade-offs** - When you make architectural decisions
5. **Production quality only** - No "TODO" or "implement later"
</execution_rules>

<action>
[Implement the full solution following the expert prompt above]
</action>
</step>

<step number="6">
<title>Validation Checklist</title>
<verify>
Before marking complete, verify:

**Role Adherence:**
- [ ] Solution reflects expert-level thinking
- [ ] Decisions explained with reasoning
- [ ] Best practices applied

**Constraint Compliance:**
- [ ] All technical constraints met
- [ ] Performance requirements satisfied
- [ ] Code quality standards achieved

**Output Format:**
- [ ] All requested deliverables present
- [ ] Documentation is complete
- [ ] Examples/tests included
</verify>

<note>If any checkbox fails, revise the solution.</note>
</step>
</workflow>

<examples>
<example name="Data Pipeline">
**Command:**
```
/expert Build real-time ETL pipeline for 10M records/hour
```

**Expert Prompt Generated:**
```
You are a Senior Data Engineer with 12 years experience in distributed
data processing, specializing in high-throughput streaming pipelines.

Your task: Build a real-time ETL pipeline for 10M records/hour

Constraints:
- Must use Apache Kafka for ingestion
- Maximum 2GB memory footprint per worker
- Sub-100ms p99 latency per record
- Zero data loss tolerance (exactly-once semantics)
- Horizontally scalable to 50M records/hour

Output format:
1. Production-ready Python code with Kafka consumer/producer
2. Unit tests (>80% coverage)
3. Integration tests with Docker Compose
4. Performance benchmark script
5. Deployment guide (Kubernetes + Helm)
6. Monitoring dashboard (Grafana + Prometheus)
```
</example>

<example name="API Endpoint">
**Command:**
```
/expert Create authenticated REST API for file uploads with virus scanning
```

**Expert Prompt Generated:**
```
You are a Senior Backend Engineer with 8 years experience in secure
API development, specializing in file handling and security.

Your task: Create authenticated REST API for file uploads with virus scanning

Constraints:
- FastAPI framework with async handlers
- JWT authentication (RS256)
- Max file size: 100MB
- Supported formats: PDF, DOCX, XLSX only
- Virus scan with ClamAV before storage
- S3-compatible storage (MinIO/AWS)
- Rate limit: 10 uploads/minute per user

Output format:
1. FastAPI application with complete endpoints
2. Authentication middleware
3. File validation and scanning logic
4. Error handling with proper HTTP codes
5. OpenAPI documentation
6. Integration tests with mocked S3 and ClamAV
7. Deployment config (Docker + docker-compose)
```
</example>

<example name="Database Optimization">
**Command:**
```
/expert Optimize slow PostgreSQL query returning 10K rows in 5 seconds
```

**Expert Prompt Generated:**
```
You are a Senior Database Engineer with 15 years experience in PostgreSQL
optimization, specializing in query performance tuning.

Your task: Optimize slow PostgreSQL query returning 10K rows in 5 seconds

Constraints:
- Target: <500ms query time
- Cannot modify table schema (production)
- Must preserve exact result set
- Read-heavy workload (1000 queries/sec)
- PostgreSQL 14

Output format:
1. Current query with EXPLAIN ANALYZE output
2. Optimized query with explanation of changes
3. Index recommendations (with DDL)
4. Before/after performance comparison
5. Monitoring query for detecting regression
6. Migration plan (zero downtime)
```
</example>
</examples>

<usage_guidance>
<when_to_use>
**Use `/expert` when:**
- Need production-quality code
- Have specific technical constraints
- Require expert-level reasoning
- Want detailed documentation
- Building critical components

**Use `/continue` when:**
- Simple, straightforward implementation
- Constraints already established in CLAUDE.md
- Following existing patterns
- Quick fixes or minor features
</when_to_use>

<pro_tips>
<tip name="Be Specific with Experience Level">
**Vague:** "You are a developer"
**Better:** "You are a Senior Python Engineer with 10 years experience"
**Best:** "You are a Principal Engineer with 15 years in distributed systems, having built 3 production platforms handling >1B requests/day"
</tip>

<tip name="Quantify Everything">
**Vague:** "Make it fast"
**Better:** "Low latency"
**Best:** "p50 <50ms, p95 <100ms, p99 <200ms"
</tip>

<tip name="Specify Output Format Exactly">
**Vague:** "Write code"
**Better:** "Write production code with tests"
**Best:** "Production-ready Python with type hints, inline docs, 80% test coverage, structured logging, and README with examples"
</tip>

<tip name="Add Domain Context">
**Generic:** "You are a Python engineer"
**Domain-Specific:** "You are a Python engineer specializing in financial systems with SOX compliance experience"
</tip>

<tip name="Combine with Other Commands">
```bash
# Plan first
/think:parallel "Build payment processing system"

# Then implement with expert constraints
/expert "Implement Stripe integration with PCI compliance constraints"

# Verify
/validate "Payment processing implementation"

# Learn
/reflect "Payment system implementation"
```
</tip>
</pro_tips>
</usage_guidance>

<advanced>
<custom_profiles>
Create reusable expert profiles in PROJECT_INDEX.json:

```json
{
  "memory": {
    "expert_profiles": {
      "backend_api": {
        "role": "Senior Backend Engineer",
        "experience": "10 years",
        "domain": "API development and microservices",
        "default_constraints": [
          "FastAPI with async handlers",
          "OpenAPI documentation",
          "80% test coverage",
          "Docker deployment"
        ]
      },
      "ml_engineer": {
        "role": "ML Engineer",
        "experience": "8 years",
        "domain": "production machine learning",
        "default_constraints": [
          "scikit-learn or PyTorch",
          "MLflow for tracking",
          "Model versioning",
          "A/B testing ready"
        ]
      }
    }
  }
}
```

Then reference: `/expert "Use backend_api profile for user authentication endpoint"`
</custom_profiles>

<integration_with_rules>
Expert constraints should complement (not contradict) your engineering rules:

**In `.claude/rules/engineering.md`:**
```markdown
## Expert Mode Defaults

When using /expert command, always apply:
- Type hints for all functions
- Structured logging (JSON format)
- Error handling with specific exceptions
- Environment-based configuration
- Prometheus metrics for monitoring
```

These become **baseline constraints** that every expert role includes.
</integration_with_rules>

<measuring_impact>
Track improvements from using `/expert`:

**Metrics to monitor:**
- Initial acceptance rate (passes on first try)
- Code review comments (should decrease)
- Bug density (issues per 1000 LOC)
- Documentation completeness
- Test coverage

**Before `/expert`:**
- Generic code requiring multiple revisions
- Missing edge cases
- Incomplete documentation
- "TODO: add error handling"

**After `/expert`:**
- Production-ready on first pass
- Edge cases handled
- Complete documentation
- No TODOs (or documented as intentional)
</measuring_impact>
</advanced>

<summary>
**The Pattern:**
```
Role + Experience + Domain + Constraints + Output Format = 10x Better Results
```

**Your Command:**
```
/expert [your task with any specifics]
```

**What You Get:**
Not "a solution" but "THE solution an expert would build."
</summary>
