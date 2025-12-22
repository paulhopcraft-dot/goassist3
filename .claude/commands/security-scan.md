---
description: Run security analysis on codebase
---

Run comprehensive security scan:

## 1. Secrets Detection

Check for hardcoded secrets:
- API keys
- Passwords
- Tokens
- Connection strings
- Private keys

```bash
# Files to check
grep -rn "password\|secret\|api_key\|token\|private_key" --include="*.py" --include="*.ts" --include="*.js" --include="*.env*" .
```

## 2. Dependency Vulnerabilities

Check for known vulnerabilities:
```bash
# Python
pip-audit

# Node.js
npm audit

# Rust
cargo audit
```

## 3. Code Security Issues

Check for:
- [ ] SQL injection (raw queries without parameterization)
- [ ] XSS vulnerabilities (unsanitized user input in HTML)
- [ ] CSRF protection missing
- [ ] Insecure deserialization
- [ ] Path traversal
- [ ] Command injection
- [ ] Insecure file uploads

## 4. Authentication & Authorization

- [ ] Auth required on all sensitive endpoints
- [ ] Password hashing (bcrypt/argon2)
- [ ] Session management secure
- [ ] CORS configured correctly
- [ ] Rate limiting present

## 5. Data Handling

- [ ] PII/sensitive data encrypted at rest
- [ ] HTTPS enforced
- [ ] Logging doesn't include secrets
- [ ] Input validation on all endpoints

## Output Format

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
