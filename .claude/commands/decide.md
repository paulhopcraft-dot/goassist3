---
description: Make high-stakes decisions with confidence weighting
---

<instructions>
Provide structured decision analysis with confidence assessment for high-stakes technical choices.
</instructions>

<decision_topic>$ARGUMENTS</decision_topic>

<analysis>
<primary_recommendation>
## 1. Primary Recommendation
- **Choice:** [Your recommended approach]
- **Reasoning:** [Why this is best given current constraints]
</primary_recommendation>

<confidence_assessment>
## 2. Confidence Assessment
- **Confidence Level:** [0-100%]
- **Confidence Factors:**
  - What we know: [supporting evidence]
  - What we don't know: [gaps in information]
  - Assumptions made: [list key assumptions]
</confidence_assessment>

<alternatives>
## 3. Alternative Approaches
**Alternative A:**
- Description: [what it is]
- Pros: [advantages]
- Cons: [disadvantages]
- When to choose: [scenarios where this is better]

**Alternative B:**
- Description: [what it is]
- Pros: [advantages]
- Cons: [disadvantages]
- When to choose: [scenarios where this is better]
</alternatives>

<confidence_boosters>
## 4. Confidence Boosters
**To increase confidence, we need:**
- [Missing information, tests, or validation needed]
- [Timeline: when could we get this]
</confidence_boosters>

<reversibility>
## 5. Reversibility Analysis
- **Switching cost:** [How hard to change later: Low/Medium/High]
- **Lock-in factors:** [What makes this sticky]
- **Exit strategy:** [How to migrate away if needed]
</reversibility>

<decision_record>
## 6. Decision Record
Document in docs/DECISIONS.md:
```markdown
## [Date] - [Decision Title]
**Status:** Accepted | Confidence: [X%]
**Context:** [Why this decision was needed]
**Decision:** [What was chosen]
**Alternatives Considered:** [Brief list]
**Consequences:** [Expected outcomes]
**Revisit:** [Date if confidence < 80%, or "N/A"]
```
</decision_record>
</analysis>

<implementation>
After documenting decision:
1. Update relevant features in features.json if needed
2. Add constraints to CLAUDE.md if applicable
3. Commit decision record
</implementation>
