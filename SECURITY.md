# Security Policy

## Supported Versions

Security fixes are handled on the default branch until the project publishes a stable release policy.

## Reporting a Vulnerability

Please report security issues privately to **Eka Syarif Maulana** at `eka.ckp16799@gmail.com` before opening a public issue. Include:

- A short description of the issue.
- Steps to reproduce or a minimal proof of concept.
- The affected commit, release, or deployment shape.
- Any known impact on API keys, cookies, host API proxying, or verification results.


Do not include real API keys, session cookies, private endpoints, or customer data in reports.

## Data Handling Notes

- Temporary API keys are intended to remain in memory for a single verification request.
- The demo server does not persist reports or API keys.
- When host API proxying is enabled, cookies are forwarded only to the configured host API.
- Operators should apply outbound network restrictions, rate limits, and request timeouts before exposing a public deployment.
