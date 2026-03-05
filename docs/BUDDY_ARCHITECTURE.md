# Buddy Agent — Cloudflare Production Architecture

> Reference documentation for the production deployment at [googleadsagent.ai](https://googleadsagent.ai).
> This describes the Cloudflare-based system. Contributors can use this as a blueprint.

---

## Overview

The production Buddy agent runs on Cloudflare's edge infrastructure, providing sub-100ms latency globally. It extends the Python-based agent with persistent state, real-time WebSocket communication, semantic memory, automated monitoring, and a credit-based billing system.

```
┌─────────────────────────────────────────────────────────┐
│                  Cloudflare Edge                         │
│                                                         │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Pages       │  │  Worker       │  │  Cron Worker │  │
│  │  (Frontend)  │  │  (Agent API)  │  │  (Scheduled)  │  │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                │                  │          │
│         │    ┌───────────┴──────────┐       │          │
│         │    │   Durable Object     │       │          │
│         │    │   (Per-user state)   │       │          │
│         │    │                      │       │          │
│         │    │  ┌──────────────┐    │       │          │
│         │    │  │ SQLite (DO)  │    │       │          │
│         │    │  │ - History    │    │       │          │
│         │    │  │ - Keys (AES) │    │       │          │
│         │    │  │ - Rollback   │    │       │          │
│         │    │  │ - Alerts     │    │       │          │
│         │    │  └──────────────┘    │       │          │
│         │    └──────────────────────┘       │          │
│         │                                   │          │
│  ┌──────┴──────────────────────────────────┴──────┐   │
│  │              Shared Storage                     │   │
│  │  KV: Sessions, Context, User data               │   │
│  │  D1: Billing (users, credits, transactions)     │   │
│  │  R2: File exports (CSV, reports)                │   │
│  │  Vectorize: Semantic memory (embeddings)        │   │
│  └────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Core Capabilities

### 1. ReAct Loop (Reason + Act)

The agent processes every user message through a multi-step reasoning loop:

```
User message
    → Intent Classification (what does the user want?)
    → Memory Retrieval (what do we already know?)
    → Tool Selection (which of 22 tools to use?)
    → Execution (call Google Ads API, web search, etc.)
    → Result Synthesis (format and present findings)
    → Memory Storage (save for future context)
```

The loop runs up to 8 iterations per message, allowing the agent to chain multiple API calls to answer complex questions.

### 2. Semantic Memory (Vectorize)

Every significant interaction is embedded and stored in Cloudflare Vectorize:

- **Conversations**: What was discussed
- **Findings**: Data discovered during analysis
- **Decisions**: Actions taken and why
- **Outcomes**: Results of write operations (tracked over time)
- **Strategies**: Recommendations and their performance

On each new message, the system retrieves the top 5 most relevant memories via cosine similarity, giving the agent persistent context across sessions.

### 3. Write Safety Protocol

All Google Ads mutations follow a strict safety flow:

1. **Propose**: Agent presents the change with a human-readable preview
2. **Confirm**: User must type "CONFIRM" explicitly
3. **Snapshot**: Pre-state captured before execution
4. **Execute**: Mutation sent to Google Ads API v22
5. **Log**: Operation recorded in rollback log with pre/post state
6. **Track**: Outcome monitored over following days

### 4. Encrypted Key Storage

User API keys (BYOK) are encrypted at rest using AES-256-GCM:

- Keys stored in Durable Object SQLite
- Encryption key from environment (`ENCRYPTION_KEY`)
- Never logged, never sent to AI providers
- Users can delete their keys at any time

### 5. Monitoring & Automation

The cron worker runs on schedule:

| Schedule     | Task                    |
|-------------|------------------------|
| Every 6h    | Health check all accounts |
| Every 12h   | Anomaly detection scan  |
| Weekly (Mon) | Performance report generation |

Alerts generated for: CPA spikes, spend drops, zero conversions, budget depletion, quality score drops.

### 6. Billing System

Credit-based system with Stripe integration:

- **Trial**: 25 free credits on signup
- **Credit packs**: Purchasable via Stripe Checkout
- **Pro subscription**: Monthly credits + priority access
- **Coupon system**: Admin-created promo codes
- **Usage metering**: Per-tool credit costs based on complexity

### 7. Multi-Provider AI

The agent supports multiple LLM providers:

| Provider   | Models                          |
|-----------|--------------------------------|
| Anthropic  | Claude Sonnet 4.6, Claude Opus 4.6 |
| OpenAI     | GPT-5.2, GPT-5.2 Pro            |
| Google     | Gemini 3 Flash, Gemini 3 Pro    |
| Workers AI | Fallback (embeddings + basic)    |

## Security Hardening (v2.0)

Applied across the Buddy production system:

1. **No hardcoded secrets** — all credentials via environment variables
2. **Session validation** — WebSocket connections require authenticated session
3. **CORS allowlist** — only production domains and localhost
4. **Rate limiting** — per-IP and per-session
5. **Input sanitization** — GAQL injection prevention, path traversal checks
6. **Generic error responses** — no internal details leaked to clients
7. **R2 access control** — file downloads require valid session
8. **Account switching validation** — users can only switch to their own accounts
9. **Encryption key required** — system refuses to encrypt/decrypt without proper key

## Google Ads API Coverage

### 22 Tools

| Tool | Capability |
|------|-----------|
| list_campaigns | List all campaigns with metrics |
| list_ad_groups | List ad groups within campaigns |
| list_keywords | List keywords with quality scores |
| list_ads | List responsive search ads |
| get_account_summary | Full account overview |
| get_campaign_details | Deep dive on single campaign |
| search_terms_report | Search query analysis |
| auction_insights | Competitor analysis |
| get_recommendations | Google's optimization suggestions |
| create_campaign | New campaign creation |
| update_campaign_status | Pause/enable campaigns |
| update_budget | Budget modifications |
| update_bids | Bid adjustments |
| add_keywords | New keyword additions |
| add_negative_keywords | Negative keyword management |
| create_ad | New ad creation |
| create_labels | Label management |
| ad_schedule | Day/time targeting |
| geo_targeting | Location targeting |
| device_adjustments | Device bid modifiers |
| change_history | Account audit trail |
| pmax_management | Performance Max campaigns |

### 65 GAQL Queries

Pre-built queries covering all major reporting dimensions: campaigns, ad groups, keywords, ads, search terms, audience segments, geographic, device, and time-based performance.

### 35+ Write Operations

Campaign creation, status changes, budget updates, bid adjustments, keyword management, ad creation, label management, targeting modifications, and more.

## How This Maps to the Python Agent

| Buddy (Cloudflare) | Python Agent (This Repo) |
|--------------------|--------------------------|
| `agent.ts` ReAct loop | `deploy/orchestrator.py` agentic loop |
| 22 TypeScript tools | 28 Python action files in `actions/` |
| Durable Object state | In-memory session dict (upgrade to Redis) |
| Vectorize memory | Not implemented (add with pgvector/Pinecone) |
| D1 billing | Not implemented (add with Stripe SDK) |
| KV sessions | In-memory dict (upgrade to Redis) |
| Cron monitoring | Not implemented (add with APScheduler/Celery) |
| WebSocket real-time | SSE streaming (add via FastAPI) |

## Contributing

The biggest gaps between Buddy and the Python agent are:

1. **Semantic memory** — Add vector storage for cross-session context
2. **Monitoring automation** — Add scheduled health checks and alerts
3. **Persistent state** — Replace in-memory dicts with Redis/PostgreSQL
4. **Streaming responses** — Add SSE endpoint for real-time tool execution feedback
5. **Billing integration** — Add Stripe for credit-based usage metering

See [CONTRIBUTING.md](../CONTRIBUTING.md) for how to get started.
