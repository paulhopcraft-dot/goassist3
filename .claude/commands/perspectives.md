---
description: Analyze decisions from multiple viewpoints
---

<instructions>
Analyze from four distinct lenses to catch blind spots in decision-making.
</instructions>

<arguments>$ARGUMENTS</arguments>

<analysis>
<technical_perspective>
## Perspective 1: Technical Feasibility

**Implementation Complexity:**
- Scope: [How much code/effort required]
- Dependencies: [New libraries, services needed]
- Technical risk: [Novel tech, unknowns]
- Skill requirements: [What expertise needed]

**Performance Implications:**
- Latency impact: [Expected change in response time]
- Resource usage: [CPU, memory, GPU, network]
- Scalability: [How does it scale]
- Bottlenecks: [Where will we hit limits]

**Technical Debt:**
- Debt created: [Shortcuts taken, cleanup needed]
- Maintenance burden: [Ongoing cost to maintain]
- Coupling introduced: [What becomes interdependent]
- Testing complexity: [How hard to test]

**Rating:** [1-10] | **Blockers:** [Major technical risks]
</technical_perspective>

<operational_perspective>
## Perspective 2: Operational Impact

**Deployment:**
- Deployment complexity: [Steps, automation needed]
- Rollback difficulty: [How easy to revert]
- Zero-downtime possible: [Yes/No, how]
- Migration path: [For existing data/users]

**Monitoring & Observability:**
- New metrics needed: [What to track]
- Alerting required: [What could go wrong]
- Debug-ability: [How to troubleshoot issues]
- Log volume: [Impact on logging costs]

**Failure Modes:**
- What breaks: [Failure scenarios]
- Blast radius: [Impact scope when it fails]
- Recovery time: [How long to restore]
- Graceful degradation: [Fallback behavior]

**Operational Cost:**
- Infrastructure: [New servers, services, $/month]
- Maintenance: [Hours/week to operate]
- On-call burden: [Incident frequency expected]

**Rating:** [1-10] | **Concerns:** [Operational risks]
</operational_perspective>

<business_perspective>
## Perspective 3: Business Value

**User Impact:**
- User benefit: [What users gain]
- User segments affected: [Who this helps]
- Pain point addressed: [What problem solved]
- Competitive advantage: [Market differentiation]

**Delivery Timeline:**
- Estimated effort: [Hours/days/weeks]
- Dependencies: [Blocking on what]
- MVP path: [Fastest shippable version]
- Incremental delivery: [Can we ship in phases]

**ROI Analysis:**
- Development cost: [Eng time * rate]
- Operational cost: [Recurring $/month]
- Expected benefit: [Revenue, retention, efficiency]
- Break-even: [When does value exceed cost]

**Prioritization:**
- Urgency: [How time-sensitive]
- Impact: [How many users affected]
- Effort: [Resource investment]
- RICE score: [(Reach * Impact * Confidence) / Effort]

**Rating:** [1-10] | **Business Risk:** [Market/revenue risks]
</business_perspective>

<future_perspective>
## Perspective 4: Future-Proofing

**Scalability Headroom:**
- Current capacity: [What it can handle now]
- Expected growth: [Usage projections]
- Bottleneck timeline: [When we hit limits]
- Scaling strategy: [Horizontal/vertical, how]

**Extension Points:**
- Pluggable architecture: [Where can we extend]
- API stability: [How locked-in is the interface]
- Configuration flexibility: [Behavior customization]
- Feature flags: [Can we toggle functionality]

**Migration Path:**
- Replaceability: [How hard to swap out later]
- Data portability: [Can we export/migrate data]
- Vendor lock-in: [Dependencies on specific providers]
- Future alternatives: [What could replace this]

**Technology Longevity:**
- Framework/library maturity: [How stable]
- Community support: [Active maintenance]
- Adoption trends: [Growing/stable/declining]
- Replacement timeline: [When might we need to rewrite]

**Rating:** [1-10] | **Future Debt:** [Long-term concerns]
</future_perspective>
</analysis>

<synthesis>
## Synthesis & Recommendation

**Perspective Scores:**
- Technical: [X/10]
- Operational: [X/10]
- Business: [X/10]
- Future: [X/10]
- **Overall:** [Average or weighted]

**Key Trade-offs:**
1. [Trade-off statement with explicit choice]
2. [Trade-off statement with explicit choice]
3. [Trade-off statement with explicit choice]

**Recommendation:**
- **Decision:** [Proceed / Proceed with modifications / Don't proceed]
- **Rationale:** [Why, given the four perspectives]
- **Conditions:** [What must be true for this to work]
- **Mitigations:** [How to address top 3 risks]

**Decision Record:**
Document in docs/DECISIONS.md with all four perspectives summarized.

**Action Items:**
1. [Specific next step based on decision]
2. [...]
</synthesis>
