---
description: Manage feature branches
---

## Branch Operations

### Create Branch
```bash
git checkout -b feature/[feature-id]-[short-name]
```

### Branch Naming Convention
- `feature/F001-user-auth` - New features
- `fix/F001-login-bug` - Bug fixes
- `refactor/F001-cleanup` - Refactoring
- `docs/F001-api-docs` - Documentation

## When to Branch

Create a new branch when:
- Starting a feature that touches >5 files
- Work might take >2 hours
- Changes are risky/experimental
- Multiple features in parallel

Stay on main when:
- Quick fix (<30 min)
- Single file change
- Documentation only

## Merge Workflow

1. Ensure all tests pass
2. Update features.json
3. Commit with conventional message
4. Merge to main:
   ```bash
   git checkout main
   git merge feature/[branch-name]
   git branch -d feature/[branch-name]
   ```

## Current Branches

```bash
git branch -a
```

$ARGUMENTS
