# Contributing to Claude Code Toolkit

Thank you for considering contributing! This toolkit is built by the community, for the community.

## Quick Links
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)

---

## Code of Conduct

Be respectful, constructive, and kind. We're all here to make development better.

---

## Getting Started

### What Can I Contribute?

- **Bug fixes**: Fix issues in commands, templates, or setup
- **New commands**: Add useful slash commands
- **Templates**: Add support for new languages/frameworks
- **Documentation**: Improve guides, examples, or clarity
- **Skills**: Add or improve Claude Code skills

### Where to Start?

1. Check [Issues](https://github.com/yourusername/claude-code-toolkit/issues) for `good-first-issue` label
2. Look for `help-wanted` labels
3. Read existing commands in `commands/` to understand patterns

---

## How to Contribute

### 1. Fork & Clone

```bash
# Fork on GitHub, then clone
git clone https://github.com/YOUR-USERNAME/claude-code-toolkit.git
cd claude-code-toolkit
```

### 2. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-123
```

### 3. Make Changes

Follow [Coding Standards](#coding-standards) below.

### 4. Test Locally

```bash
# Test setup wizard
cd /tmp/test-project
bash /path/to/your-fork/setup-wizard.sh

# Test commands work
claude
/project:status
/your-new-command
```

### 5. Commit

Use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git commit -m "feat: add database migration templates"
git commit -m "fix: setup wizard copies skills correctly"
git commit -m "docs: improve BRANCHING-STRATEGY examples"
```

### 6. Push & Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

---

## Development Setup

### Prerequisites

- Bash (for setup wizard)
- Git
- Claude Code CLI installed

### Repository Structure

```
claude-code-toolkit/
├── commands/           # Slash commands (add new ones here)
├── templates/          # Project templates
│   ├── .github/        # CI/CD workflows
│   ├── tests/          # Test templates
│   └── ...
├── skills/             # Claude Code skills
├── docs/               # Documentation
└── setup-wizard.sh     # Setup script
```

---

## Coding Standards

### Slash Commands

**Format**: Markdown with YAML frontmatter

```markdown
---
description: Brief description (shows in /help)
---

# Command Name

Brief explanation of what this does.

## Usage

\`\`\`bash
/command [arguments]
\`\`\`

## Examples

\`\`\`bash
/command example1
/command example2
\`\`\`

$ARGUMENTS
```

**Rules**:
- Keep commands focused (do one thing well)
- Include clear examples
- Use `$ARGUMENTS` to accept user input
- Add to appropriate category in `/help` command

### Templates

**Rules**:
- Must work out-of-the-box
- Include comments explaining non-obvious parts
- Follow language-specific best practices
- Test with actual project setup

### Skills

**Format**: Markdown with YAML frontmatter

```markdown
---
name: skill-name
description: What this skill does
---

# Skill Name

Instructions for Claude Code...
```

**Rules**:
- Clear, actionable instructions
- No ambiguity
- Examples where helpful

### Shell Scripts

**Rules**:
- Use `set -e` for safety
- Add comments for complex logic
- Handle errors gracefully
- Test on macOS, Linux, and Windows (Git Bash)

---

## Testing

### Manual Testing Checklist

Before submitting PR, test:

- [ ] **Setup wizard works**
  - New project (empty directory)
  - Existing project (with code)
  - Multiple stacks (Python, Node, Go)

- [ ] **Commands install correctly**
  - All 30+ commands present
  - Skills install correctly
  - No duplication

- [ ] **Templates validate**
  - JSON schema passes
  - CI/CD workflows run
  - Test files work

- [ ] **Cross-platform**
  - Works on macOS/Linux
  - Works on Windows (Git Bash)

### Test Script (Coming Soon)

We're working on automated tests. For now, manual testing required.

---

## Documentation

### Update When Changing:

| Change | Update These Files |
|--------|-------------------|
| Add command | `commands/`, `commands/help.md`, `README.md` |
| Add template | `templates/`, `README.md`, `TOOLKIT-OVERVIEW.md` |
| Add skill | `skills/`, `README.md` |
| Breaking change | `CHANGELOG.md`, migration guide |
| Setup wizard | `setup-wizard.sh`, `README.md` |

### Documentation Style

- **Be concise**: No fluff
- **Use examples**: Show, don't just tell
- **Use tables**: For lists of options/commands
- **Use code blocks**: With syntax highlighting
- **Be specific**: "Run `npm test`" not "run tests"

---

## Pull Request Process

### 1. Before Submitting

- [ ] Code follows standards above
- [ ] Tested manually (see checklist)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No merge conflicts with main
- [ ] Commit messages follow Conventional Commits

### 2. PR Description

Use the [PR template](.github/PULL_REQUEST_TEMPLATE.md):
- Describe what changed
- Link related issues
- Show screenshots/examples if applicable
- List breaking changes (if any)

### 3. Review Process

1. Maintainer reviews within 2-3 days
2. Address feedback (if any)
3. Maintainer approves & merges
4. Your contribution is live! 🎉

### 4. After Merge

- Your branch will be deleted
- Changes appear in next release
- You're listed in contributors

---

## Release Process

(For maintainers)

### Versioning

We use [SemVer](https://semver.org/):
- **MAJOR**: Breaking changes (v2.0.0 → v3.0.0)
- **MINOR**: New features (v2.0.0 → v2.1.0)
- **PATCH**: Bug fixes (v2.0.0 → v2.0.1)

### Release Checklist

1. Update `CHANGELOG.md` with version
2. Create git tag: `git tag v2.1.0`
3. Push tag: `git push origin v2.1.0`
4. GitHub Release with changelog notes

---

## Questions?

- Open an [Issue](https://github.com/yourusername/claude-code-toolkit/issues)
- Check [Discussions](https://github.com/yourusername/claude-code-toolkit/discussions)
- Read [TOOLKIT-OVERVIEW.md](TOOLKIT-OVERVIEW.md)

---

## Thank You! 🙏

Every contribution makes this toolkit better for everyone. We appreciate your time and effort.

Happy coding with Claude! 🚀
