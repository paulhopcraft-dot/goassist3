---
name: worktree
version: 1.0.0
description: Manage Git worktrees for isolated feature development
---

# Git Worktree Management: $ARGUMENTS

## Overview

Manage isolated workspaces for safe feature development. Each feature gets its own sandbox - main branch stays pristine.

---

## Commands

### Create: `/worktree create <feature-id>`

Create new isolated workspace:

```bash
# Parse arguments
FEATURE_ID="$1"
BASE_BRANCH="${2:-main}"
WORKTREE_ROOT="../worktrees"
BRANCH_NAME="feature/$FEATURE_ID"
WORKTREE_PATH="$WORKTREE_ROOT/$FEATURE_ID"

# Ensure base is up to date
git fetch origin
git checkout $BASE_BRANCH
git pull origin $BASE_BRANCH

# Create feature branch
git checkout -b $BRANCH_NAME $BASE_BRANCH

# Create worktree
git worktree add $WORKTREE_PATH $BRANCH_NAME

# Output
echo "✓ Created worktree: $WORKTREE_PATH"
echo "✓ Branch: $BRANCH_NAME"
echo "✓ Based on: $BASE_BRANCH"
```

**Output**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Worktree Created
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Feature: F001-user-auth
Path: ../worktrees/F001-user-auth
Branch: feature/F001-user-auth
Base: main (abc1234)

You are now in an isolated workspace.
Main branch is protected.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### Switch: `/worktree switch <feature-id>`

Switch to existing worktree:

```bash
FEATURE_ID="$1"
WORKTREE_PATH="../worktrees/$FEATURE_ID"

# Check exists
if [ ! -d "$WORKTREE_PATH" ]; then
    echo "❌ Worktree not found: $FEATURE_ID"
    echo "Use /worktree list to see available worktrees"
    exit 1
fi

# Change directory context
cd "$WORKTREE_PATH"
echo "✓ Switched to: $WORKTREE_PATH"
echo "Branch: $(git branch --show-current)"
```

---

### List: `/worktree list`

Show all active worktrees:

```bash
git worktree list
```

**Output**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Active Worktrees
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/c/Dev/project              main         [main]
/c/Dev/worktrees/F001-auth  abc1234      [feature/F001-auth]
/c/Dev/worktrees/F002-api   def5678      [feature/F002-api]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### Merge: `/worktree merge <feature-id> [--squash]`

Merge feature back to main:

```bash
FEATURE_ID="$1"
SQUASH="${2:-}"
BRANCH_NAME="feature/$FEATURE_ID"
WORKTREE_PATH="../worktrees/$FEATURE_ID"

# Switch to main
git checkout main
git pull origin main

# Merge
if [ "$SQUASH" = "--squash" ]; then
    git merge --squash $BRANCH_NAME
    git commit -m "feat: $FEATURE_ID (squashed)"
else
    git merge --no-ff $BRANCH_NAME -m "Merge $BRANCH_NAME into main"
fi

# Push
git push origin main

# Cleanup
git worktree remove $WORKTREE_PATH
git branch -d $BRANCH_NAME

echo "✓ Merged and cleaned up: $FEATURE_ID"
```

**Output**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Feature Merged
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Feature: F001-user-auth
Merged to: main
Method: merge (--no-ff)
Commits: 5

Cleanup:
✓ Removed worktree: ../worktrees/F001-user-auth
✓ Deleted branch: feature/F001-user-auth
✓ Pushed to origin
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### Cleanup: `/worktree cleanup <feature-id>`

Remove worktree without merging:

```bash
FEATURE_ID="$1"
WORKTREE_PATH="../worktrees/$FEATURE_ID"
BRANCH_NAME="feature/$FEATURE_ID"

# Remove worktree
git worktree remove $WORKTREE_PATH --force

# Optionally delete branch
read -p "Delete branch $BRANCH_NAME? (y/N): " confirm
if [ "$confirm" = "y" ]; then
    git branch -D $BRANCH_NAME
fi

echo "✓ Cleaned up: $FEATURE_ID"
```

---

### Cleanup Stale: `/worktree cleanup-stale`

Remove worktrees for merged/deleted branches:

```bash
# Prune stale worktree references
git worktree prune

# List remaining
git worktree list
```

---

## Integration with Features.json

When creating/merging worktrees, update features.json:

```json
{
  "features": [
    {
      "id": "F001",
      "name": "User Authentication",
      "status": "in_progress",
      "passes": false,
      "worktree": {
        "path": "../worktrees/F001-user-auth",
        "branch": "feature/F001-user-auth"
      }
    }
  ]
}
```

After merge, remove worktree field and update status.

---

## Conflict Handling

If merge has conflicts:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ Merge Conflict Detected
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Feature: F001-user-auth
Conflicting files:
  - src/auth/login.ts
  - src/auth/register.ts

Options:
  1. /resolve           - AI-assisted resolution
  2. /resolve --preview - See proposed changes
  3. git merge --abort  - Cancel merge

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Best Practices

1. **One feature per worktree** - Keep changes focused
2. **Commit frequently** - Small, atomic commits in worktree
3. **Pull main before merge** - Minimize conflicts
4. **Test before merge** - Run full test suite in worktree
5. **Cleanup promptly** - Don't accumulate stale worktrees

---

## Example Workflow

```bash
# Start new feature
/worktree create F001-user-auth

# Work in isolation (automatically in worktree context)
# ... make changes ...
npm test
git add .
git commit -m "feat(auth): add login endpoint"

# Ready to merge
/worktree merge F001-user-auth

# Or with squash
/worktree merge F001-user-auth --squash
```

---

**Execute the requested worktree operation.**
