---
description: Initialize project with features list and tracking files
---

You are the INITIALIZER AGENT for this project.

Read @spec.md thoroughly, then:

1. **Create features.json** with 50-200 specific, testable features
   - Mark ALL features as "passes": false initially
   - Features should be granular (e.g., "user can click login button")
   - Include acceptance_criteria for each feature
   - Order by dependencies

2. **Create claude-progress.txt**
   - Start with: "Session 1 (Initializer): Set up project structure"

3. **Create architecture.md**
   - Document technical decisions
   - Explain the structure

4. **Create init.sh** (if applicable)
   - Script to start dev environment
   - Install dependencies
   - Run smoke test

5. **Set up testing framework** if not present

6. **Make initial git commit**

Think hard about the feature list - be comprehensive. This determines everything.

After completion, report:
- Total features created
- Recommended build order
- Any blockers or questions
