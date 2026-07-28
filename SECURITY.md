# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Reporting a Vulnerability

If you discover a security vulnerability in devpub, **please do not open a public issue.**

Instead, report it by emailing: **simplynadaf@gmail.com**

Include:
- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### What to expect

- Acknowledgment within 48 hours
- Assessment and fix within 7 days for critical issues
- Credit in the release notes (unless you prefer anonymity)

### Scope

Security issues we care about:
- API key exposure through logs, error messages, or unexpected file writes
- Command injection through article content or filenames
- Dependency vulnerabilities with known exploits
- Unintended network requests leaking user data

### Out of scope

- Issues in the Dev.to API itself (report those to Forem)
- Denial of service through rate limiting (that's by design)
- Issues requiring physical access to the machine
