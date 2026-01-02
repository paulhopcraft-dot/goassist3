/**
 * Security scan hook: Auto-trigger on sensitive file changes
 * Monitors auth, env, and security-related files
 */

module.exports = {
  name: 'security-scan-trigger',
  description: 'Auto-trigger security scan on sensitive files',
  type: 'PostToolUse',

  // Match edits to security-sensitive files
  match: (toolName, input) => {
    if (!['Edit', 'Write'].includes(toolName)) return false;

    const path = (input.file_path || '').toLowerCase();
    const sensitivePatterns = [
      '.env',
      'auth',
      'login',
      'password',
      'secret',
      'token',
      'api-key',
      'apikey',
      'credential',
      'payment',
      'stripe',
      'encryption',
      'crypto'
    ];

    return sensitivePatterns.some(pattern => path.includes(pattern));
  },

  onComplete: async (context, result) => {
    return {
      action: 'required',
      message: 'AUTO-SECURITY: Sensitive file modified. Security scan required.',
      command: '/security-scan'
    };
  }
};
