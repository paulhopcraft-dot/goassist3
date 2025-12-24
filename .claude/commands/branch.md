---
description: Manage feature branches
---

<branch_operations>
<create_branch>
```bash
git checkout -b feature/[feature-id]-[short-name]
```
</create_branch>

<naming_convention>
- `feature/F001-user-auth` - New features
- `fix/F001-login-bug` - Bug fixes
- `refactor/F001-cleanup` - Refactoring
- `docs/F001-api-docs` - Documentation
</naming_convention>
</branch_operations>

<branching_strategy>
<when_to_branch>
Create a new branch when:
- Starting a feature that touches >5 files
- Work might take >2 hours
- Changes are risky/experimental
- Multiple features in parallel
</when_to_branch>

<stay_on_main>
Stay on main when:
- Quick fix (<30 min)
- Single file change
- Documentation only
</stay_on_main>
</branching_strategy>

<merge_workflow>
<steps>
1. Ensure all tests pass
2. Update features.json
3. Commit with conventional message
4. Merge to main:
   ```bash
   git checkout main
   git merge feature/[branch-name]
   git branch -d feature/[branch-name]
   ```
</steps>
</merge_workflow>

<current_branches>
```bash
git branch -a
```
</current_branches>

<arguments>$ARGUMENTS</arguments>
