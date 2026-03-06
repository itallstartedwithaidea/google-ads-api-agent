# Changelog

## v2.1.0 — 2026-03-05 (Comprehensive Wiki + Capability Documentation)

### Wiki (15 pages)
- **Home** — Navigation hub with full capability comparison (Repo vs MCP vs Buddy)
- **Quick Start** — Install, configure, run in 5 minutes
- **Credentials Setup** — Google Ads, Anthropic, Cloudinary, SearchAPI, Gemini
- **Architecture Overview** — System design, data flow, ReAct loop, CEP protocol
- **Buddy Architecture** — Cloudflare production: Durable Objects, Agents SDK, D1, R2, Vectorize
- **Tool Reference** — All 21 tools overview with parameters
- **Read Tools** — All 47 GAQL query types documented
- **Write Tools** — All 62 mutation operations with CEP safety
- **AI Tools** — Web search, keyword research, URL scanning, PageSpeed, creative builder
- **Sub-Agents** — 6 specialists: Simba, Nemo, Elsa, Aladdin, Moana, Baymax
- **GAQL Query Reference** — Full SQL for all 47 queries
- **Mutation Reference** — Detailed parameter tables for all 62 writes
- **Security** — CORS, rate limiting, AES-256-GCM encryption, CEP protocol, SSRF, XSS
- **API Endpoints** — Python REST API + Cloudflare Pages Functions reference
- **Troubleshooting** — Common issues, debugging tips, getting help

### Documentation Updates
- Updated `BUDDY_ARCHITECTURE.md` with accurate tool count (21 tools, 47 reads, 62 writes)
- Added complete tool inventory table replacing abbreviated 22-tool list
- Updated Python-to-Buddy mapping table with Merchant Center, URL scanning, PageSpeed, creative builder
- Fixed GAQL query count from "65" to accurate "47"
- Fixed write operations count from "35+" to accurate "62"

### Capability Audit Results
Full audit confirmed Buddy production system covers all 23 MCP tools plus:
- 24 additional GAQL read queries
- 51 additional write operations
- 12 AI-powered tools (search, keywords, URL scan, PageSpeed, creative, planning, export)
- Semantic memory (Vectorize)
- Real-time WebSocket (Agents SDK)
- Credit billing (D1 + Stripe)
- Encrypted BYOK storage (AES-256-GCM)
- Merchant Center integration (5 operations)
- Automated monitoring (daily health, weekly reports, outcome tracking)

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
