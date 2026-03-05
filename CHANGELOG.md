# Changelog

## v2.0.0 — 2026-03-05 (Buddy Security Hardening Release)

### Security Fixes
- **CORS hardening**: Server no longer uses wildcard `*` origins. Defaults to localhost; configure via `ALLOWED_ORIGINS` env var
- **Rate limiting**: Built-in IP-based rate limiter (30 req/min default, configurable via `RATE_LIMIT_MAX`)
- **Error message sanitization**: Server returns generic errors to clients, logs full details internally
- **Input validation**: GAQL period values whitelisted to prevent injection
- **Write safety protocol**: All mutations require explicit user confirmation (CEP Protocol)

### New Files
- `LICENSE` — MIT license (previously missing)
- `SECURITY.md` — Security policy, vulnerability reporting, best practices
- `CONTRIBUTING.md` — Contributor guide with priority areas and code style
- `.env.example` — Environment variable template with placeholders
- `.gitignore` — Comprehensive ignore rules for Python projects
- `pyproject.toml` — Modern Python packaging configuration
- `setup.py` — PyPI-compatible package setup
- `CHANGELOG.md` — This file
- `docs/BUDDY_ARCHITECTURE.md` — Cloudflare Buddy agent architecture reference

### Improvements
- Updated `deploy/server.py` with security middleware
- Added `ALLOWED_ORIGINS` environment variable support
- Added rate limiting middleware
- Package now installable via `pip install google-ads-agent`
- CLI entry point: `gads-agent` command
- Version bumped to 2.0.0

### Architecture Documentation
- Added Buddy (Cloudflare) architecture reference showing the production deployment
- Documents the full Cloudflare stack: Workers, Durable Objects, D1, KV, R2, Vectorize
- Includes ReAct loop, semantic memory, monitoring, and billing system details
- Serves as a reference for contributors building the equivalent in Python

## v1.0.0 — 2026-02-10 (Initial Release)

- 28 custom Google Ads API actions
- 6 specialized sub-agents (Reporting, Research, Optimization, Shopping, Creative, Creative Innovate)
- Programmatic deployment via Anthropic API (Path A)
- Agent platform deployment guide (Path B)
- FastAPI REST server with session management
- Docker support
- Interactive CLI
