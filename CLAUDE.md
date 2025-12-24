# GoAssist3 - Claude Code Configuration

## Autonomous Mode: ENABLED

**User Preference: Operate autonomously with proactive command usage.**

### Automatic (No Permission Required):
- `/prd-check` - Before any changes to documented features
- `/verify` - After completing features
- `/constraints` - For complex features upfront
- Task agents - For efficiency (exploration, verification)
- `/project:status` - When resuming work

### Suggest & Execute:
- `/decide` - High-stakes decisions (announce, then execute)
- `/perspectives` - Major architectural choices (announce, then execute)
- `/project:handoff` - End of session (suggest first)

### Never Without Asking:
- Destructive operations (delete, force push)
- Major architectural changes
- Changing project structure

## Project Overview

Voice assistant with 30+ slash commands for full development workflow automation.
Tracks features via features.json with red→green verification.
