# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT open a public GitHub issue**
2. Email: john@itallstartedwithaidea.com
3. Include: description, steps to reproduce, potential impact
4. We'll respond within 48 hours

## Security Practices

### Credentials

- **Never commit API keys** — use `.env` files (gitignored) or secrets managers
- **Rotate keys** if you suspect exposure — even in private repos
- All credentials reference `.env` via `python-dotenv`; the `.env.example` contains only placeholders

### CORS

- The FastAPI server defaults to `localhost` origins only
- Set `ALLOWED_ORIGINS` env var to a comma-separated list of your actual domains
- **Never use `*` in production**

### Rate Limiting

- Built-in IP-based rate limiting (default: 30 req/min)
- Configure via `RATE_LIMIT_MAX` env var
- For production, add API key authentication

### Input Validation

- GAQL queries use parameterized patterns to prevent injection
- All Google Ads API calls use the official `google-ads` Python SDK which handles escaping
- Period/date range values are whitelisted where user-supplied

### Write Safety

- All write operations (campaign creation, bid changes, budget adjustments) use the **CEP Protocol**:
  - **Confirm**: Agent presents what it will do
  - **Execute**: Only after explicit user confirmation
  - **Post-check**: Verify the operation succeeded
- Pre-state snapshots captured before mutations

### Error Handling

- Server logs full error details internally
- Client receives generic error messages (no stack traces, no internal paths)

## Supported Versions

| Version | Supported |
|---------|-----------|
| 2.x     | Yes       |
| 1.x     | No        |

## Dependencies

Run `pip audit` regularly to check for known vulnerabilities in dependencies.
