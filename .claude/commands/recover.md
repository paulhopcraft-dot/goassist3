---
description: Recover from errors or corrupted state
---

# Project Recovery

Diagnose and fix common project issues.

## Diagnostics

Run full health check:

### 1. Git Health
```bash
git status
git log --oneline -5
git remote -v
```

Check for:
- Uncommitted changes
- Detached HEAD
- Merge conflicts
- Unpushed commits

### 2. Features.json Health
- Valid JSON syntax
- Schema compliance
- Metadata counts match actual features
- No duplicate IDs
- All dependencies exist
- Timestamps valid

### 3. Dependencies Health
- Lock files present (package-lock.json, requirements.txt, go.sum)
- No dependency conflicts
- Security vulnerabilities check

### 4. File System Health
- CLAUDE.md present
- claude-progress.txt present
- Test files exist
- Build artifacts clean

## Recovery Actions

### Fix Corrupted features.json

**Symptoms:**
- JSON parse errors
- Invalid schema
- Mismatched counts

**Recovery:**
1. Validate JSON syntax
2. Check against schema
3. Offer to auto-fix:
   - Sync metadata counts
   - Fix timestamps
   - Remove invalid fields
4. Create backup before fixing

### Reset Feature Status

**Symptoms:**
- Feature marked passing but tests fail
- Need to re-verify features

**Recovery:**
```bash
# Reset single feature
/recover feature F005

# Reset all features to pending
/recover all-features

# Reset only failed test features
/recover failed-features
```

### Fix Git Issues

**Symptoms:**
- Merge conflicts
- Detached HEAD
- Corrupted commits

**Recovery:**
1. Check git status
2. Offer solutions:
   - Abort merge: `git merge --abort`
   - Reattach HEAD: `git checkout main`
   - Stash changes: `git stash`
   - Hard reset: `git reset --hard origin/main` (DANGEROUS)

### Rebuild Dependencies

**Symptoms:**
- Import errors
- Missing packages
- Dependency conflicts

**Recovery:**
```bash
# Python
rm -rf venv/ __pycache__/
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Node
rm -rf node_modules/ package-lock.json
npm install

# Go
go mod tidy
go mod download
```

### Clean Build Artifacts

```bash
# Python
rm -rf build/ dist/ *.egg-info __pycache__/ .pytest_cache/

# Node
rm -rf dist/ build/ out/

# Go
go clean -cache -testcache -modcache
```

## Safety Checks

Before any destructive operation:

1. **Confirm with user**: Show what will be deleted/changed
2. **Create backup**: Save current state
3. **Verify git status**: Ensure no uncommitted work lost

## Recovery Modes

### Safe Recovery (Default)
- Non-destructive fixes only
- Creates backups
- Asks for confirmation

### Force Recovery (Use with Caution)
- Can delete files
- Resets state
- Requires explicit confirmation

Use `$ARGUMENTS` to specify recovery mode and target.

## Examples

```bash
/recover                          # Full diagnostic scan
/recover features.json            # Fix features.json only
/recover git                      # Fix git issues
/recover dependencies             # Rebuild dependencies
/recover --force                  # Force recovery (dangerous)
```

## Post-Recovery

After recovery:
1. Run `/project:status` to verify state
2. Run tests to ensure functionality
3. Update claude-progress.txt with recovery notes
4. Commit recovery changes if needed
