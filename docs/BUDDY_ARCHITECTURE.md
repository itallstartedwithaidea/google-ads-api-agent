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
    → Tool Selection (which of 21 tools to use?)
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

### 21 Tools

| Tool | Capability |
|------|-----------|
| pull_google_ads_data | 47 GAQL read queries (campaigns, keywords, search terms, audiences, etc.) |
| execute_google_ads_action | 62 write operations with CEP safety |
| execute_google_ads_batch | Batch mutations in phased execution |
| compare_performance | Period-over-period performance comparison |
| generate_keyword_ideas | Google Keyword Planner API |
| upload_offline_conversions | CRM conversion import via GCLID |
| upload_customer_match | Email/phone list audience upload |
| undo_last_write | Rollback info for last mutation |
| search_web | Google Search, Trends, Ads Transparency Center via SearchAPI |
| analyze_keywords | SERP-based keyword research |
| scan_url | URL analysis (GA4, GTM, Meta, consent, SEO) |
| fetch_pagespeed | PageSpeed Insights / Core Web Vitals |
| build_creative | AI ad copy generation (RSA, PMax, Display, Social) |
| review_image | AI vision analysis of creative assets |
| propose_action_plan | Structured action plan with risk assessment |
| create_plan | Multi-step execution plan with dependencies |
| calculate | Deterministic ad math (budget, ROAS, CPA, forecasts) |
| verify_output | Self-verification (character limits, math, data) |
| export_file | CSV data export |
| save_document / load_document | Persistent document storage (audits, strategies, reports) |
| manage_tasks | Task list management |
| search_memory | Semantic search over past conversations (Vectorize) |

### 47 GAQL Read Queries

Pre-built queries covering: account summary, campaigns, ad groups, ads, keywords, search terms, wasted spend, quality scores, audiences (6 types), demographics (4 types), device, geographic, auction insights, impression share, change history, recommendations, conversions, landing pages, video campaigns/ads, shopping, PMax (asset groups, assets, listing groups), placements, topics, schedules, labels, bidding strategies, experiments, extensions, negative keyword lists, campaign criteria, shared budgets, daily/hourly/campaign-daily performance.

### 62 Write Operations

Campaign CRUD (6 channel types), budget management (4 ops), ad group CRUD, RSA + display ad management, keyword management (6 ops), 8 extension types (sitelink, callout, snippet, call, price, promotion, lead form, image), label management, audience targeting, placement/topic targeting, content exclusions, bid modifiers (device, location), ad scheduling, IP exclusions, conversion action management, experiments (create, start, end/promote), PMax asset groups + assets, image/text asset uploads, recommendations (apply, dismiss), batch operations (up to 20 per request), and 5 Merchant Center operations (product CRUD + status).

## How This Maps to the Python Agent

| Buddy (Cloudflare) | Python Agent (This Repo) |
|--------------------|--------------------------|
| `brain.js` + `gads.js` ReAct loop | `deploy/orchestrator.py` agentic loop |
| `agent.ts` Durable Object agent | — (stateless) |
| 21 TypeScript tools, 47 reads, 62 writes | 28 Python action files in `actions/` |
| Durable Object SQLite state | In-memory session dict (upgrade to Redis) |
| Vectorize semantic memory | Not implemented (add with pgvector/Pinecone) |
| D1 billing with Stripe | Not implemented (add with Stripe SDK) |
| KV sessions + context | In-memory dict (upgrade to Redis) |
| `onTask` scheduled monitoring | Not implemented (add with APScheduler/Celery) |
| WebSocket real-time (Agents SDK) | SSE streaming (add via FastAPI) |
| Merchant Center integration (5 ops) | Not implemented |
| URL scanning (GA4, GTM, Meta, consent) | Not implemented |
| PageSpeed Insights | Not implemented |
| AI creative builder | Not implemented |

## Contributing

The biggest gaps between Buddy and the Python agent are:

1. **Semantic memory** — Add vector storage for cross-session context
2. **Monitoring automation** — Add scheduled health checks and alerts
3. **Persistent state** — Replace in-memory dicts with Redis/PostgreSQL
4. **Streaming responses** — Add SSE endpoint for real-time tool execution feedback
5. **Billing integration** — Add Stripe for credit-based usage metering

See [CONTRIBUTING.md](../CONTRIBUTING.md) for how to get started.
