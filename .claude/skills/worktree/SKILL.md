---
name: worktree
description: Git Worktree Isolation - safe feature development in isolated workspaces
version: 1.0.0
source: Auto-Claude integration (v3.4)
---

# Worktree Skill - Isolated Feature Development

You are now in **Worktree Mode** - manage isolated Git workspaces for safe feature development.

## Mission

Enable safe, parallel feature development:
- **Never touch main branch** during development
- **Isolated workspace** per feature
- **Clean merge** back when ready
- **Auto-cleanup** of stale worktrees

**Key Principle**: Each feature gets its own sandbox. Main stays pristine.

---

## Commands

### Create Worktree
```bash
/worktree create <feature-id> [base-branch]
```

Creates an isolated workspace for a feature:
1. Creates feature branch from base (default: main)
2. Creates worktree directory at `../worktrees/<feature-id>`
3. Registers in worktree-config.json
4. Switches context to new worktree

**Example**:
```bash
/worktree create F001-user-auth
# Creates: ../worktrees/F001-user-auth/
# Branch: feature/F001-user-auth
```

### Switch Worktree
```bash
/worktree switch <feature-id>
```

Switch to an existing worktree's context.

### List Worktrees
```bash
/worktree list
```

Show all active worktrees with status.

### Merge Worktree
```bash
/worktree merge <feature-id> [--squash]
```

Merge feature back to main:
1. Switch to main
2. Pull latest
3. Merge feature branch (or squash)
4. Push
5. Cleanup worktree

### Cleanup Worktree
```bash
/worktree cleanup <feature-id>
```

Remove worktree and optionally delete branch.

### Cleanup All
```bash
/worktree cleanup-stale
```

Remove worktrees for merged/deleted branches.

---

## Process

### Creating a Worktree

```bash
# 1. Ensure we're in the main repo
cd /path/to/project

# 2. Create feature branch
git checkout -b feature/F001-user-auth main

# 3. Create worktree directory
git worktree add ../worktrees/F001-user-auth feature/F001-user-auth

# 4. Register in config
# Update .claude/v3/worktrees/worktree-config.json

# 5. Confirm
echo "Worktree created at ../worktrees/F001-user-auth"
echo "Working on branch: feature/F001-user-auth"
```

### Working in a Worktree

```bash
# Switch to worktree
cd ../worktrees/F001-user-auth

# Work normally - all changes isolated
npm test
git add .
git commit -m "feat(auth): add login endpoint"

# Push feature branch
git push -u origin feature/F001-user-auth
```

### Merging a Worktree

```bash
# Switch back to main repo
cd /path/to/project

# Ensure main is up to date
git checkout main
git pull origin main

# Merge feature (or squash)
git merge feature/F001-user-auth --no-ff
# OR: git merge --squash feature/F001-user-auth

# Push
git push origin main

# Cleanup
git worktree remove ../worktrees/F001-user-auth
git branch -d feature/F001-user-auth
```

---

## Configuration

### worktree-config.json

```json
{
  "worktrees": {
    "F001-user-auth": {
      "path": "../worktrees/F001-user-auth",
      "branch": "feature/F001-user-auth",
      "base": "main",
      "created": "2025-12-27T10:00:00Z",
      "status": "active",
      "feature_id": "F001",
      "description": "User authentication system"
    }
  },
  "settings": {
    "worktree_root": "../worktrees",
    "branch_prefix": "feature/",
    "auto_push": true,
    "cleanup_merged": true
  }
}
```

---

## Integration with Autonomous Mode

When `/autonomous` performs risky operations:

```
PHASE 3: Execute Action

IF action is risky (major refactor, experimental feature):
  1. Create worktree: /worktree create AUTO-001-refactor
  2. Execute in worktree
  3. Run tests
  4. IF tests pass:
     - /worktree merge AUTO-001-refactor
  5. ELSE:
     - Log failure
     - /worktree cleanup AUTO-001-refactor
     - Main branch untouched ✓
```

---

## Integration with Features.json

When creating a worktree for a feature:

```json
{
  "features": [
    {
      "id": "F001",
      "name": "User Authentication",
      "status": "in_progress",
      "worktree": {
        "path": "../worktrees/F001-user-auth",
        "branch": "feature/F001-user-auth",
        "created": "2025-12-27"
      }
    }
  ]
}
```

---

## Safety Rules

### NEVER in Worktree Mode:
- Force push to main
- Delete main branch
- Merge untested code
- Leave stale worktrees indefinitely

### ALWAYS:
- Create worktree for experimental work
- Run tests before merge
- Clean up after merge
- Keep worktree-config.json updated

---

## Error Handling

### Worktree Already Exists
```json
{
  "status": "error",
  "error_type": "worktree_exists",
  "feature_id": "F001-user-auth",
  "existing_path": "../worktrees/F001-user-auth",
  "action": "Use /worktree switch F001-user-auth or cleanup first"
}
```

### Merge Conflicts
```json
{
  "status": "conflict",
  "error_type": "merge_conflict",
  "feature_id": "F001-user-auth",
  "conflicting_files": ["src/auth.ts", "src/user.ts"],
  "action": "Use /resolve to handle conflicts"
}
```

### Dirty Worktree
```json
{
  "status": "warning",
  "error_type": "uncommitted_changes",
  "feature_id": "F001-user-auth",
  "uncommitted_files": 3,
  "action": "Commit or stash changes before switching"
}
```

---

## Example Session

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/worktree create F001-user-auth
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Creating isolated workspace for F001-user-auth...

✓ Created branch: feature/F001-user-auth (from main)
✓ Created worktree: ../worktrees/F001-user-auth
✓ Registered in worktree-config.json
✓ Updated features.json

Workspace Ready:
  Path: ../worktrees/F001-user-auth
  Branch: feature/F001-user-auth
  Base: main (commit abc123)

You are now working in the isolated worktree.
Main branch is protected - all changes are sandboxed.

To merge when ready: /worktree merge F001-user-auth

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Platform Commands

### Windows (PowerShell)
```powershell
# Create worktree
git worktree add ..\worktrees\F001-user-auth feature/F001-user-auth

# List worktrees
git worktree list

# Remove worktree
git worktree remove ..\worktrees\F001-user-auth
```

### macOS/Linux (Bash)
```bash
# Create worktree
git worktree add ../worktrees/F001-user-auth feature/F001-user-auth

# List worktrees
git worktree list

# Remove worktree
git worktree remove ../worktrees/F001-user-auth
```

---

## Benefits

1. **Safety**: Main branch never touched during development
2. **Parallelism**: Multiple features in progress simultaneously
3. **Clean History**: Squash messy commits on merge
4. **Easy Rollback**: Just delete worktree, main is clean
5. **CI-Friendly**: Each worktree can run its own tests

---

**GO! Create an isolated worktree for safe feature development.**
