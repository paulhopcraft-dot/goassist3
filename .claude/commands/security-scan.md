---
description: Run security analysis on codebase
---

<instructions>
Run comprehensive security scan covering secrets detection, dependency vulnerabilities, code security issues, authentication/authorization, and data handling.
</instructions>

<scan_categories>
<category name="Secrets Detection">
<description>Check for hardcoded secrets:</description>
<items>
- API keys
- Passwords
- Tokens
- Connection strings
- Private keys
</items>
<command>
```bash
# Files to check
grep -rn "password\|secret\|api_key\|token\|private_key" --include="*.py" --include="*.ts" --include="*.js" --include="*.env*" .
```
</command>
</category>

<category name="Dependency Vulnerabilities">
<description>Check for known vulnerabilities:</description>
<commands>
```bash
# Python
pip-audit

# Node.js
npm audit

# Rust
cargo audit
```
</commands>
</category>

<category name="Code Security Issues">
<checklist>
- [ ] SQL injection (raw queries without parameterization)
- [ ] XSS vulnerabilities (unsanitized user input in HTML)
- [ ] CSRF protection missing
- [ ] Insecure deserialization
- [ ] Path traversal
- [ ] Command injection
- [ ] Insecure file uploads
</checklist>
</category>

<category name="Authentication & Authorization">
<checklist>
- [ ] Auth required on all sensitive endpoints
- [ ] Password hashing (bcrypt/argon2)
- [ ] Session management secure
- [ ] CORS configured correctly
- [ ] Rate limiting present
</checklist>
</category>

<category name="Data Handling">
<checklist>
- [ ] PII/sensitive data encrypted at rest
- [ ] HTTPS enforced
- [ ] Logging doesn't include secrets
- [ ] Input validation on all endpoints
</checklist>
</category>
</scan_categories>

<output_format>
```
Security Scan Results
=====================

🔴 Critical:
- [Must fix immediately]

🟠 High:
- [Fix before production]

🟡 Medium:
- [Fix soon]

🟢 Info:
- [Best practice suggestions]

Summary: [X critical, Y high, Z medium issues]
```
</output_format>
