# Changelog

All notable changes to Claude Code Toolkit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub issue templates (bug report, feature request)
- Pull request template
- CONTRIBUTING.md with development guidelines
- Pre-commit hooks configuration
- VSCode workspace settings and recommended extensions
- Docker templates (Dockerfile, docker-compose.yml)
- Database migration templates (Alembic, Prisma, golang-migrate)

## [2.0.0] - 2025-12-23

### Added
- **JSON Schema Validation**: features.json now validates against schema automatically
- **Test Templates**: Ready-to-use test setups for Python (pytest), TypeScript/Node (Vitest/Jest), and Go
- **CI/CD Workflows**: GitHub Actions templates with security scanning for Python and Node.js
- **Recovery Commands**: `/recover` command to diagnose and fix broken states, corrupted files, git issues
- **Validation Command**: `/validate-features` with schema checking and auto-fix capabilities
- **Help System**: `/help` command with search functionality to find commands by keyword
- **Comprehensive .gitignore**: Multi-stack gitignore covering Python, Node, Go, Rust with security best practices
- **Environment Template**: .env.example with all common services (Supabase, AWS, OpenAI, Stripe, etc.)
- **Branching Strategy Guide**: Complete guide in docs/BRANCHING-STRATEGY.md covering trunk-based and git-flow
- **Frontend Design Skill**: Anthropic's official UI design skill for distinctive interfaces

### Changed
- **Setup Wizard**: Now automatically copies all 30+ commands and skills (previously only created 4 basic commands)
- **Setup Wizard**: Auto-detects toolkit location for reliable installation
- **Command Organization**: Removed .claude/commands duplication, commands/ is now single source of truth
- **LICENSE**: Updated with proper copyright holder
- **README.md**: Added v2.0 features section with comprehensive command listing
- **TOOLKIT-OVERVIEW.md**: Updated structure to reflect new templates and organization

### Fixed
- Setup wizard now correctly copies all commands and skills
- Command installation process is fully automated
- Features.json now includes schema reference for validation

### Enhanced
- pytest.ini with coverage, markers, logging, and best practices
- features.json template with schema reference and extended fields
- Documentation with production-ready examples
- Error messages and diagnostic output

## [1.0.0] - 2025-12-13

### Added
- Initial release of Claude Code Toolkit
- Core slash commands: continue, status, verify, handoff, review, branch, add-feature
- PRD enforcement commands: prd-check, build-prd, edit-prd, design-prd
- Decision-making commands: decide, constraints, perspectives
- Thinking commands: think, think-parallel, anticipate, reflect
- Context management commands: context, fresh, reload, last
- Delegation commands: delegate, expert, index
- features.json tracking system with red→green pattern
- CLAUDE.md template for project instructions
- claude-progress.txt for session continuity
- setup-wizard.sh for automated project setup
- engineering-mode skill with global code quality standards
- prompt-spec-ready.md for Browser Claude integration
- prompt-existing-project.md for retrofitting existing codebases
- prompt-harness.md for long-running agent patterns
- BEGINNERS-GUIDE.md for non-technical users
- QUICK-REFERENCE.md cheat sheet
- TOOLKIT-OVERVIEW.md comprehensive documentation

### Core Concepts
- Red → Green pattern (features start with passes: false)
- Session continuity through progress tracking
- Browser Claude (Opus) for planning, Claude Code (Sonnet) for building
- Verification-first approach (never mark complete without testing)
- JSON-based feature tracking over markdown

---

## Version History Summary

| Version | Date | Major Changes |
|---------|------|---------------|
| 2.0.0 | 2025-12-23 | Production-ready: schemas, tests, CI/CD, recovery tools |
| 1.0.0 | 2025-12-13 | Initial release with 30+ commands and core workflow |

---

## Migration Guides

### Migrating from 1.0 to 2.0

**Breaking Changes**: None - v2.0 is fully backward compatible

**New Features to Adopt**:
1. **Add schema to existing features.json**:
   ```json
   {
     "$schema": "./features.schema.json",
     ...
   }
   ```

2. **Copy new templates**:
   ```bash
   cp toolkit/templates/features.schema.json your-project/
   cp toolkit/templates/.gitignore your-project/
   cp toolkit/templates/.env.example your-project/
   ```

3. **Use new commands**:
   - `/validate-features` - Check your features.json
   - `/recover` - Fix issues when things break
   - `/help` - Find commands quickly

4. **Optional: Add CI/CD**:
   ```bash
   cp -r toolkit/templates/.github/ your-project/
   ```

5. **Optional: Add test templates**:
   ```bash
   cp -r toolkit/templates/tests/python/ your-project/tests/
   # or typescript, go depending on your stack
   ```

---

## Links

- [GitHub Repository](https://github.com/yourusername/claude-code-toolkit)
- [Issues](https://github.com/yourusername/claude-code-toolkit/issues)
- [Discussions](https://github.com/yourusername/claude-code-toolkit/discussions)
