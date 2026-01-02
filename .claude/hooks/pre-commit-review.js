/**
 * Pre-commit hook: Enforce code review before commits
 * This hook runs before any git commit and ensures /review was run
 */

module.exports = {
  name: 'pre-commit-review',
  description: 'Ensures code review before commits',

  // Runs before git commit commands
  match: (toolName, input) => {
    if (toolName === 'Bash') {
      const cmd = input.command || '';
      return cmd.includes('git commit');
    }
    return false;
  },

  // Check if review was recently run (within last 10 tool calls)
  validate: async (context) => {
    const recentTools = context.recentToolCalls || [];
    const hasRecentReview = recentTools.some(call =>
      call.name === 'Skill' && call.input?.skill === 'review'
    );

    if (!hasRecentReview) {
      return {
        allow: false,
        message: 'AUTO-REVIEW REQUIRED: Run /review before committing.'
      };
    }

    return { allow: true };
  }
};
