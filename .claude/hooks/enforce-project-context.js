/**
 * Post-response hook: Enforce [PROJECT: name] on every response
 * This is a validation hook that checks response format
 */

module.exports = {
  name: 'enforce-project-context',
  description: 'Ensures every response starts with [PROJECT: folder-name]',
  type: 'PostToolUse',

  // Check after any tool that produces output
  match: (toolName) => {
    return ['Read', 'Bash', 'Grep', 'Glob'].includes(toolName);
  },

  // Reminder to include project context
  onComplete: async (context) => {
    const projectName = context.workingDirectory?.split(/[/\\]/).pop() || 'unknown';
    return {
      reminder: `Remember: Start response with [PROJECT: ${projectName}]`
    };
  }
};
