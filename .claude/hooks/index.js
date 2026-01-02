/**
 * Claude Code Toolkit Hooks
 *
 * These hooks enforce toolkit rules automatically:
 * - Pre-commit review enforcement
 * - Project context reminders
 * - Auto-test on source changes
 * - Security scan on sensitive files
 */

module.exports = {
  hooks: [
    require('./pre-commit-review'),
    require('./enforce-project-context'),
    require('./auto-test-trigger'),
    require('./security-scan-trigger')
  ]
};
