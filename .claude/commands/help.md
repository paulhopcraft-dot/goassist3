---
description: Search and display help for available commands
---

# Command Help & Search

Find the right command for your task.

## Usage

```bash
/help                    # Show all commands
/help [keyword]          # Search commands by keyword
/help [command-name]     # Show detailed help for specific command
```

## Available Commands

### Core Workflow
| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/project:continue` | Work on next feature | Daily workflow |
| `/project:status` | Show progress | Check what's done/pending |
| `/project:handoff` | Save session state | End of coding session |
| `/project:verify` | Test all features | Before release/deploy |

### Feature Management
| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/project:add-feature` | Add to backlog | New requirement arrives |
| `/project:init-project` | Initialize from spec | Starting new project |
| `/validate-features` | Check features.json | Debugging tracking issues |

### Code Quality
| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/project:review` | Code review | After major changes |
| `/project:security-scan` | Security check | Before production |
| `/project:tdd` | Test-driven dev | Building new feature with tests |

### Branching & Git
| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/project:branch` | Manage branches | Creating/merging features |
| `/worktree` | Isolated workspaces | Safe feature development (v3.4) |
| `/resolve` | AI merge resolution | Fix merge conflicts (v3.4) |
| `/recover` | Fix git/project issues | Something's broken |

### Memory & Context (v3.4)
| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/remember` | Save to memory | Store decisions, learnings, context |
| `/recall` | Load from memory | Retrieve past context |
| `/status --board` | Kanban board view | Visual task overview |

### PRD & Requirements
| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/prd-check` | Verify PRD alignment | Before starting work |
| `/build-prd` | Build with PRD enforcement | Regulated projects |
| `/edit-prd` | Edit with PRD validation | Modifying existing features |
| `/design-prd` | Design within PRD constraints | Architecture decisions |

### Decision Making
| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/decide` | High-stakes decisions | Choosing between options |
| `/constraints` | Define boundaries | Before complex features |
| `/perspectives` | Multi-viewpoint analysis | Major architectural choices |

### Thinking & Planning
| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/think` | Extended thinking | Complex problems |
| `/think-parallel` | Parallel reasoning | Exploring multiple approaches |
| `/anticipate` | Predict issues | Risk assessment |
| `/reflect` | Review decisions | Post-mortem analysis |

### Context Management
| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/context` | Manage context window | Approaching token limits |
| `/fresh` | Start fresh context | New session |
| `/reload` | Reload project context | After long break |
| `/last` | Resume from last session | Continuing work |

### Delegation & Expertise
| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/delegate` | Delegate to specialist | Need specific expertise |
| `/expert` | Consult domain expert | Technical deep dive |

### Documentation
| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/index` | Generate project index | Understanding codebase |

## Search Examples

```bash
/help git          # Find git-related commands
/help test         # Find testing commands
/help prd          # Find PRD commands
/help branch       # Find branching commands
/help recover      # Find recovery/fix commands
```

## Quick Tips

### New to the Project?
1. `/project:status` - See what's done
2. `/index` - Understand structure
3. `/project:continue` - Start working

### Starting a Feature?
1. `/prd-check` - Verify alignment (if using PRDs)
2. `/constraints` - Define boundaries (if complex)
3. `/project:branch create` - Create feature branch
4. `/project:continue` - Implement

### Stuck or Broken?
1. `/recover` - Diagnose issues
2. `/help recover` - See recovery options
3. `/validate-features` - Check features.json
4. `/project:status` - Verify state

### Before Merging?
1. `/project:verify` - Test all features
2. `/project:review` - Code review
3. `/project:security-scan` - Security check
4. `/project:branch merge` - Merge when ready

### Using Worktrees (v3.4)?
1. `/worktree create F001` - Isolated workspace
2. Build safely (main protected)
3. `/worktree merge F001` - Merge back
4. `/resolve` - If conflicts arise

## Command Aliases

If arguments provided as `$ARGUMENTS`:
- Search keywords in command descriptions
- Show matching commands
- Display detailed help for exact matches

## Getting More Help

- See `QUICK-REFERENCE.md` for cheat sheet
- See `TOOLKIT-OVERVIEW.md` for full documentation
- See specific command files in `.claude/commands/` for details
