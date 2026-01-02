/**
 * Post-edit hook: Auto-run tests after code changes
 * Triggers test run after editing source files
 */

module.exports = {
  name: 'auto-test-trigger',
  description: 'Auto-run tests after editing source files',
  type: 'PostToolUse',

  // Match Edit/Write on source files (not tests, not config)
  match: (toolName, input) => {
    if (!['Edit', 'Write'].includes(toolName)) return false;

    const path = input.file_path || '';
    const isSourceFile = /\.(ts|js|tsx|jsx|py|go)$/.test(path);
    const isTestFile = /\.(test|spec)\.(ts|js|tsx|jsx)$/.test(path) || path.includes('__tests__');
    const isConfig = /\.(json|md|yml|yaml)$/.test(path);

    return isSourceFile && !isTestFile && !isConfig;
  },

  onComplete: async (context, result) => {
    return {
      action: 'suggest',
      message: 'AUTO-TEST: Source file modified. Run tests to verify changes.',
      command: 'npm test'
    };
  }
};
