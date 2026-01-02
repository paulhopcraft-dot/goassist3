# Claude Code Toolkit - Lite Edition

5 essential commands for the global `claude` CLI.

## Commands

| Command | Purpose |
|---------|---------|
| `/status` | Check project state |
| `/continue` | Resume work on next task |
| `/autonomous` | Work without interruption |
| `/review` | Quick code review |
| `/handoff` | End session cleanly |

## Install Globally

Copy to your home directory's `.claude/commands/` folder:

### Windows (PowerShell)
```powershell
# Create global commands folder
mkdir -Force "$env:USERPROFILE\.claude\commands"

# Copy lite commands
Copy-Item ".\*.md" "$env:USERPROFILE\.claude\commands\" -Exclude "README.md"
```

### macOS/Linux
```bash
# Create global commands folder
mkdir -p ~/.claude/commands

# Copy lite commands
cp ./*.md ~/.claude/commands/
rm ~/.claude/commands/README.md
```

## Usage

From any directory, run:
```bash
claude
```

Then use any command:
```
/status
/continue
/autonomous
/review
/handoff
```

## Comparison: Lite vs Full Toolkit

| Aspect | Lite (5 commands) | Full (40+ commands) |
|--------|-------------------|---------------------|
| Setup | Copy 5 files | Full project structure |
| Context | ~500 tokens | ~5000+ tokens |
| Use case | Quick tasks | Large projects |
| Learning curve | 5 minutes | 30+ minutes |

## When to Use Full Toolkit

Upgrade to full toolkit when you need:
- PRD-driven development (`/build-prd`)
- Feature tracking (`features.json`)
- Self-learning patterns
- Domain-specific compliance
- Worktree isolation

Get full toolkit: https://github.com/your-repo/claude-code-toolkit
