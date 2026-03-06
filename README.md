# Google Ads API Agent

[![Release](https://img.shields.io/github/v/release/itallstartedwithaidea/google-ads-api-agent)](https://github.com/itallstartedwithaidea/google-ads-api-agent/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

An enterprise-grade, AI-powered Google Ads management system with **250 custom API actions**, **and multiple specialized tools**, and **live read/write access** to Google Ads accounts via the Google Ads API v22.

The production version runs at **[googleadsagent.ai](https://googleadsagent.ai)** (Buddy) on Cloudflare's edge — with semantic memory, encrypted key storage, automated monitoring, and a credit-based billing system. This repo is the open-source Python agent that powers the same capabilities.

---

## What's New in v2.0

- **Security hardening** — CORS restrictions, rate limiting, error sanitization, GAQL injection prevention
- **Installable package** — `pip install google-ads-agent` (or download from [Releases](https://github.com/itallstartedwithaidea/google-ads-api-agent/releases))
- **MIT License** — proper open-source licensing
- **Production architecture docs** — full Cloudflare Buddy reference in [`docs/BUDDY_ARCHITECTURE.md`](docs/BUDDY_ARCHITECTURE.md)
- **Security policy** — [`SECURITY.md`](SECURITY.md) with vulnerability reporting and best practices
- **Contributor guide** — [`CONTRIBUTING.md`](CONTRIBUTING.md) with priority areas and code style
- **Environment template** — [`.env.example`](.env.example) with all credential placeholders

See the full [CHANGELOG](CHANGELOG.md) for details.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Three Deployment Paths](#three-deployment-paths)
- [Path A: Deploy via the Anthropic API](#path-a-deploy-via-the-anthropic-api)
- [Path B: Deploy on an Agent Platform](#path-b-deploy-on-an-agent-platform-manual-ui)
- [Path C: Cloudflare Production (Buddy)](#path-c-cloudflare-production-buddy)
- [Repository Structure](#repository-structure)
- [Prerequisites](#prerequisites)
- [Step 1: Obtain API Credentials](#step-1-obtain-api-credentials)
  - [1A: Google Ads API](#1a-google-ads-api-credentials)
  - [1B: Cloudinary](#1b-cloudinary-credentials)
  - [1C: SearchAPI.io](#1c-searchapiio-credentials)
  - [1D: Google AI (Gemini)](#1d-google-ai--gemini-credentials)
- [Step 2–7: Agent Platform Setup](#step-2-create-the-main-agent)
- [Validation & Testing](#step-7-validation--testing)
- [Credential Patterns Reference](#credential-patterns-reference)
- [Architecture Overview](#architecture-overview)
- [Security](#security)
- [Known Issues](#known-issues)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## Quick Start

```bash
# Option 1: Install as a package
pip install google-ads-agent

# Option 2: Clone and install from source
git clone https://github.com/itallstartedwithaidea/google-ads-api-agent.git
cd google-ads-api-agent
pip install -r requirements.txt

# Configure credentials
cp .env.example .env
# Edit .env with your API keys (see Step 1 below)

# Validate setup
python scripts/validate.py

# Run the interactive agent
python scripts/cli.py

# Or start the REST API server
uvicorn deploy.server:app --port 8000

# Or run with Docker
docker compose up
```

---

## Three Deployment Paths

| Path | Best For | What You Need |
|------|----------|---------------|
| **A: Anthropic API (Programmatic)** | Production apps, SaaS, automation pipelines | Anthropic API key + Python |
| **B: Agent Platform (Manual UI)** | Quick prototyping, single-user, visual builder | Agent platform account |
| **C: Cloudflare Production (Buddy)** | Full-stack with memory, billing, monitoring | Cloudflare account |

**Path A** is what this repo provides out of the box. Path C is the production system at [googleadsagent.ai](https://googleadsagent.ai) — see [`docs/BUDDY_ARCHITECTURE.md`](docs/BUDDY_ARCHITECTURE.md) for the full architecture.

### What Buddy Adds (Path C)

| Capability | Technology |
|-----------|-----------|
| Per-user persistent state | Durable Objects + SQLite |
| Semantic memory | Vectorize embeddings |
| Encrypted BYOK storage | AES-256-GCM |
| Real-time WebSocket | Cloudflare Agents SDK |
| Automated monitoring | Cron Workers |
| Credit-based billing | D1 + Stripe |
| Multi-provider AI | Claude, GPT, Gemini routing |
| File exports | R2 object storage |

---

## Path A: Deploy via the Anthropic API

This is the **programmatic deployment** — no manual UI, no clicking. Everything runs through Claude's Messages API with tool use.

### How It Works

The action files in this repo were originally built for an agent platform. The `deploy/` package adapts them to run standalone via the Anthropic API. Here's what happens under the hood when you run `python scripts/cli.py`:

```
YOU: "Show me campaigns for Acme Corp"
 │
 ▼
┌─────────────────────────────────────────────────────────────────┐
│  orchestrator.py — sends to Anthropic Messages API:             │
│                                                                 │
│  client.messages.create(                                        │
│      model="claude-opus-4-5-20251101",                          │
│      system=<your system prompt from prompts/>,                 │
│      tools=<28 tool JSON schemas from tool_schemas.py>,         │
│      messages=[{"role": "user", "content": "Show me..."}]       │
│  )                                                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼ Claude returns stop_reason="tool_use"
┌─────────────────────────────────────────────────────────────────┐
│  Claude's response:                                             │
│  tool_use: name="campaign_adgroup_manager"                      │
│            input={"action": "list_campaigns",                   │
│                    "search": "Acme Corp",                       │
│                    "status_filter": "ENABLED"}                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  tool_executor.py — the adapter layer:                          │
│                                                                 │
│  1. Loads actions/main-agent/09_campaign_adgroup_manager.py     │
│  2. Injects secrets={"DEVELOPER_TOKEN": "...", ...}             │
│     into module namespace (replicating agent platform runtime)    │
│  3. Suppresses subprocess pip install calls                     │
│  4. Inspects run() signature, drops any extra params            │
│  5. Calls: run(action="list_campaigns", search="Acme Corp",    │
│              status_filter="ENABLED")                           │
│  6. Returns JSON result to orchestrator                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  orchestrator.py — sends tool_result back to Claude:            │
│                                                                 │
│  messages.append({"role": "user", "content": [{                 │
│      "type": "tool_result",                                     │
│      "tool_use_id": "toolu_xxx",                                │
│      "content": "<JSON campaign data>"                          │
│  }]})                                                           │
│                                                                 │
│  → Loop repeats until Claude returns final text                 │
└─────────────────────────────────────────────────────────────────┘
```

**What the adapter layer (`tool_executor.py`) solves:**

| Problem | What the action files do | What the adapter does |
|---------|------------------------|----------------------|
| **Secrets** | Reference `secrets["KEY"]` as a bare global injected by the agent platform | Injects `secrets` dict into module `__dict__` before `exec_module()` |
| **Pip installs** | Run `subprocess.check_call(["pip", "install", "google-ads"])` at import time | Monkey-patches subprocess to skip pip commands (deps already in `requirements.txt`) |
| **Parameter mismatch** | 26/28 `run()` functions have explicit params (no `**kwargs`) | Inspects `run()` signature via `inspect.signature()`, drops any params Claude sends that aren't in the function |

### A-1: Get Your Anthropic API Key

1. Go to **[Anthropic Console](https://console.anthropic.com)**
2. Sign up or log in
3. Go to **[Settings → API Keys](https://console.anthropic.com/settings/keys)**
4. Click **Create Key**
5. Copy the key → this is your `ANTHROPIC_API_KEY`

> 💡 The key starts with `sk-ant-api03-...`. Store it securely — it grants full API access.

**How this ties into the system:** Every call to Claude's Messages API requires this key in the `x-api-key` header. The `anthropic` Python SDK reads it from `ANTHROPIC_API_KEY` env var automatically.

### A-2: Install & Run (Python)

**What happens, step by step, when you run this:**

```bash
# 1. Clone — gets all 66 files: action code, prompts, schemas, adapter layer
git clone https://github.com/YOUR_USERNAME/google-ads-api-agent.git
cd google-ads-agent

# 2. Virtual env — isolates dependencies
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install deps — this is what replaces the inline pip installs
#    google-ads, anthropic, fastapi, cloudinary, etc. all install here
pip install -r requirements.txt

# 4. Configure — the .env file feeds all 5 services' credentials
cp .env.example .env
# Edit .env — you need at minimum:
#   ANTHROPIC_API_KEY (to talk to Claude)
#   GOOGLE_ADS_* keys (to talk to Google Ads API)
#   Others are optional depending on which tools you use

# 5. Validate — checks files exist, imports work, credentials are set,
#    optionally makes a live API call to verify Claude responds
python scripts/validate.py

# 6. Run the agent — this starts the agentic loop:
#    Your message → Claude + 28 tool schemas → tool_use → execute → repeat
python scripts/cli.py
```

**After step 6, you'll see:**
```
┌─────────────────────────────────────────┐
│    Google Ads API Agent — Interactive CLI    │
│    Type 'quit' to exit, 'reset' to      │
│    clear conversation history            │
└─────────────────────────────────────────┘
  Model: claude-opus-4-5-20251101
  Tools: 28 loaded

You: Show me an account summary for Acme Corp
  [thinking...]

Agent: Here's the account summary for Acme Corp (ID: 123-456-7890):
       Total Spend (Last 30 Days): $12,345.67
       Active Campaigns: 8
       ...
```

That's it. The agent is running, making real Google Ads API calls through your credentials, with Claude orchestrating which tools to call and how to interpret the results.

### A-3: Use in Your Own Code

```python
from dotenv import load_dotenv
load_dotenv()

from deploy import create_agent_system

# Create the full agent with all 28 tools + sub-agents
agent = create_agent_system()

# Single question
response = agent.chat("Show me an account summary for Acme Corp")
print(response)

# Multi-turn conversation (history is maintained automatically)
response = agent.chat("Drill into the top campaign by spend")
print(response)

# Reset conversation when done
agent.reset_conversation()
```

### A-4: Deploy as a REST API

The included FastAPI server gives you HTTP endpoints for any frontend or integration:

```bash
# Start the server
uvicorn deploy.server:app --host 0.0.0.0 --port 8000

# Or with Docker
docker compose up
```

**Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/chat` | Send a message, get a response (auto-creates session) |
| `POST` | `/sessions` | Create a new conversation session |
| `GET` | `/sessions/{id}` | Get session info and message count |
| `DELETE` | `/sessions/{id}` | Delete a session |
| `GET` | `/health` | Health check (credential status) |
| `GET` | `/tools` | List all 28 tools and their file status |

**Example request:**

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "List all campaigns for Acme Corp", "session_id": "optional-session-id"}'
```

**Example response:**

```json
{
  "response": "Here are the active campaigns for Acme Corp (ID: 123-456-7890):\n\n1. Brand Search — $1,234.56 spend, 89 conversions...",
  "session_id": "abc-123-def",
  "tool_calls_made": 2
}
```

### A-5: Deploy with Docker

```bash
# Build and run
docker compose up -d

# Scale to multiple instances
docker compose up -d --scale agent=3

# Run the CLI interactively
docker compose run cli

# Run validation
docker compose run validate
```

### A-6: Scaling Considerations

| Concern | Current State | Production Upgrade |
|---------|--------------|-------------------|
| **Sessions** | In-memory dict | Swap to Redis — add `redis` service in docker-compose, replace `sessions` dict with Redis client |
| **Rate limits** | Anthropic API limits per tier | Add request queuing with `celery` or `asyncio.Semaphore` |
| **Multi-tenant** | Single credential set | Load credentials per-tenant from a secrets manager (AWS Secrets Manager, HashiCorp Vault) |
| **Auth** | None | Add API key middleware or OAuth2 to the FastAPI server |
| **Monitoring** | Basic logging | Add structured logging + export to Datadog/CloudWatch |
| **Cost control** | None | Track token usage via `response.usage` and set budget alerts |
| **Retry logic** | SDK default (2 retries) | Tune `max_retries` and add exponential backoff for Google Ads API calls |

### A-7: Known Gotchas

Things that might trip you up on first run:

| Issue | What Happens | Fix |
|-------|-------------|-----|
| **google-ads import fails** | Action files need `google-ads>=28.1.0` which has C dependencies | Run `pip install -r requirements.txt` first — this is why the adapter suppresses inline pip installs |
| **`secrets` KeyError** | An action tries to access a credential you didn't set in `.env` | Check which credential pattern the tool uses (A/B/C/D) and verify `.env` has those keys |
| **TypeError on run()** | Claude sends a param the run() function doesn't accept | The param filter should catch this — if it doesn't, check `python -c "from deploy import ToolExecutor; print(ToolExecutor().get_run_signature('tool_name'))"` |
| **Rate limits** | Google Ads API Basic Access = 15K ops/day, 4 req/sec | Use `cost_min`, `status`, `limit` params to reduce result sets |
| **First load is slow** | Module loading + pip suppression adds ~1-2s on first tool call | Subsequent calls use cached modules — instant |
| **Token costs** | claude-opus-4-5 with 28 tool definitions = ~4K tokens per request just for tools | For cost optimization, switch to `claude-sonnet-4-5-20250929` in the constructor |

### A-8: The Deploy Package — File Reference

```
deploy/
├── __init__.py          ← Package exports
├── tool_schemas.py      ← All 28 tools in Anthropic tool_use JSON Schema format
├── tool_executor.py     ← Maps tool_use calls → action Python files, injects credentials
├── orchestrator.py      ← Agentic loop: send → tool_use → execute → return → repeat
└── server.py            ← FastAPI REST API with session management

scripts/
├── cli.py               ← Interactive terminal agent
└── validate.py           ← Deployment validation (files, imports, credentials, live API)
```

---

## Path B: Deploy on an Agent Platform (Manual UI)

If you prefer a visual builder (OpenAI, or similar), follow Steps 2–7 below. You'll paste system prompts, action code, and credentials into the platform's UI.

---

```
google-ads-agent/
├── README.md                          ← You are here
├── .env.example                       ← Template for all required credentials
├── .gitignore
├── requirements.txt                   ← Python dependencies
├── Dockerfile                         ← Container build
├── docker-compose.yml                 ← Multi-service orchestration
│
├── deploy/                            ← PROGRAMMATIC DEPLOYMENT (Path A)
│   ├── __init__.py
│   ├── tool_schemas.py                ← 28 tools in Anthropic JSON Schema format
│   ├── tool_executor.py               ← Maps tool_use → action files + credential injection
│   ├── orchestrator.py                ← Agentic loop: Claude ↔ tools ↔ sub-agents
│   └── server.py                      ← FastAPI REST API with session management
│
├── scripts/
│   ├── cli.py                         ← Interactive terminal agent
│   └── validate.py                    ← Deployment validation suite
│
├── actions/
│   ├── main-agent/                    ← 28 Python action files for the main agent
│   │   ├── 01_label_manager.py
│   │   ├── 02_conversion_tracking_manager.py
│   │   ├── 03_audience_manager.py
│   │   ├── ...
│   │   └── 28_pmax_asset_group_manager.py
│   │
│   └── sub-agents/
│       ├── reporting/                 ← 8 action files for Reporting sub-agent
│       │   ├── 01_performance_reporter.py
│       │   ├── 02_search_terms_analyzer.py
│       │   ├── ...
│       │   └── 08_package_installer.py
│       ├── research/                  ← 4 action files for Research sub-agent
│       │   ├── 01_keyword_planner.py
│       │   ├── 02_google_search_api.py
│       │   ├── 03_ads_transparency_center.py
│       │   └── 04_google_trends_analyzer.py
│       ├── creative/                  ← 2 action files for Creative sub-agent
│       │   ├── 01_responsive_display_ads_manager.py
│       │   └── 02_demand_gen_ads_manager.py
│       └── creative-innovate/         ← 2 action files for Baymax — Creative Innovate
│           ├── 01_cloudinary_tools.py
│           └── 02_gemini_vision.py
│
├── prompts/
│   ├── main_agent_system_prompt.md    ← Full system prompt for the main agent
│   └── sub-agents/
│       ├── 01_reporting_analysis.md
│       ├── 02_research_intelligence.md
│       ├── 03_optimization.md
│       ├── 04_shopping_pmax.md
│       ├── 05_creative.md
│       └── 06_creative_innovate.md
│
├── configs/
│   └── agent_registry.json            ← Complete agent/action metadata & IDs
│
└── docs/
    └── ARCHITECTURE.md                ← Full technical architecture document
```

---

## Prerequisites

Before you begin, you'll need:

| Requirement | Why | Cost |
|-------------|-----|------|
| **Anthropic API key** | Powers the Claude agent via the Messages API | Pay-per-use ([pricing](https://docs.anthropic.com/en/docs/about-claude/pricing)) |
| **Google Ads account** | API access to manage campaigns | Free (ads spend separate) |
| **Google Ads Manager (MCC) account** | Multi-account access | Free |
| **Google Cloud Platform project** | OAuth2 credentials for the Google Ads API | Free tier available |
| **Cloudinary account** | Image/video processing for creative assets | Free tier (25 credits/mo) |
| **SearchAPI.io account** | Real-time Google search, Trends, Ads Transparency | Free tier (100 searches/mo) |
| **Google AI Studio account** | Gemini API for AI creative generation | Free tier available |
| **Agent platform account** | Where you deploy the agent (e.g., OpenAI, or similar) | Varies |

---

## Step 1: Obtain API Credentials

You need credentials from **4 services**. This section walks through each one with exact URLs, screenshots guidance, and what to copy.

---

### 1A: Google Ads API Credentials

This is the most complex setup. You need **5 values** that work together:

| Credential | What It Is | Where It Lives |
|------------|-----------|----------------|
| `DEVELOPER_TOKEN` | Your API access key from Google Ads | Google Ads UI |
| `CLIENT_ID` | OAuth2 app identifier | Google Cloud Console |
| `CLIENT_SECRET` | OAuth2 app secret | Google Cloud Console |
| `REFRESH_TOKEN` | Long-lived OAuth2 token | Generated via OAuth flow |
| `LOGIN_CUSTOMER_ID` | Your MCC account ID | Google Ads UI |

#### Step 1A-1: Get Your Developer Token

1. Go to **[Google Ads](https://ads.google.com)** and sign in with your Manager (MCC) account
2. Click the **Tools & Settings** icon (wrench) in the top navigation
3. Under **Setup**, click **API Center**
   - If you don't see API Center, you may need to request access first
4. Your **Developer Token** is displayed on this page
5. **Token Access Level:**
   - `Test Account` — works only with test accounts (good for development)
   - `Basic Access` — up to 15,000 operations/day (apply for this)
   - `Standard Access` — unlimited (apply after proving usage)
6. **Copy the token** → this is your `GOOGLE_ADS_DEVELOPER_TOKEN`

> ⚠️ If your token shows "Pending" status, you can still use it with test accounts. For production, you need to [apply for Basic Access](https://developers.google.com/google-ads/api/docs/access-levels).

#### Step 1A-2: Create OAuth2 Credentials in Google Cloud

1. Go to **[Google Cloud Console](https://console.cloud.google.com)**
2. Create a new project (or select an existing one):
   - Click the project dropdown at top → **New Project**
   - Name: `google-ads-agent` (or whatever you prefer)
   - Click **Create**
3. **Enable the Google Ads API:**
   - Go to **[APIs & Services → Library](https://console.cloud.google.com/apis/library)**
   - Search for `Google Ads API`
   - Click on it → Click **Enable**
4. **Configure the OAuth Consent Screen:**
   - Go to **[APIs & Services → OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent)**
   - Select **External** (unless you have Google Workspace, then Internal)
   - Fill in:
     - App name: `Google Ads Agent`
     - User support email: your email
     - Developer contact: your email
   - Click **Save and Continue**
   - **Scopes:** Click **Add or Remove Scopes** → search for `Google Ads API` → check `https://www.googleapis.com/auth/adwords` → **Update** → **Save and Continue**
   - **Test Users:** Add your Google Ads account email → **Save and Continue**
   - Click **Back to Dashboard**
5. **Create OAuth2 Client ID:**
   - Go to **[APIs & Services → Credentials](https://console.cloud.google.com/apis/credentials)**
   - Click **+ Create Credentials** → **OAuth client ID**
   - Application type: **Web application**
   - Name: `Google Ads Agent`
   - Authorized redirect URIs: Add `http://localhost:8080` (needed for the token generation step)
   - Click **Create**
   - **Copy the Client ID** → this is your `GOOGLE_ADS_CLIENT_ID`
   - **Copy the Client Secret** → this is your `GOOGLE_ADS_CLIENT_SECRET`

#### Step 1A-3: Generate a Refresh Token

The refresh token lets the agent authenticate without user interaction. You generate it once and it lasts indefinitely (unless revoked).

**Option A: Using Google's OAuth2 Playground (Easiest)**

1. Go to **[OAuth 2.0 Playground](https://developers.google.com/oauthplayground/)**
2. Click the **gear icon** ⚙️ (top right)
   - Check **Use your own OAuth credentials**
   - Enter your `Client ID` and `Client Secret` from Step 1A-2
   - Close the settings
3. In the left panel, scroll to **Google Ads API v18** → check `https://www.googleapis.com/auth/adwords`
4. Click **Authorize APIs**
5. Sign in with the Google account that has access to your Google Ads accounts
6. Grant the requested permissions
7. Click **Exchange authorization code for tokens**
8. **Copy the Refresh Token** → this is your `GOOGLE_ADS_REFRESH_TOKEN`

**Option B: Using the google-ads Python library**

```bash
pip install google-ads

# Run the built-in auth helper
python -m google_ads.auth.generate_user_credentials \
  --client_id=YOUR_CLIENT_ID \
  --client_secret=YOUR_CLIENT_SECRET
```

This opens a browser for OAuth consent and prints the refresh token.

**Option C: Using curl**

```bash
# 1. Get authorization code (open this URL in browser)
echo "https://accounts.google.com/o/oauth2/v2/auth?client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost:8080&response_type=code&scope=https://www.googleapis.com/auth/adwords&access_type=offline&prompt=consent"

# 2. After authorizing, grab the 'code' parameter from the redirect URL

# 3. Exchange code for refresh token
curl -X POST https://oauth2.googleapis.com/token \
  -d "code=AUTHORIZATION_CODE" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "redirect_uri=http://localhost:8080" \
  -d "grant_type=authorization_code"

# The response JSON contains your refresh_token
```

#### Step 1A-4: Get Your Login Customer ID (MCC)

1. Go to **[Google Ads](https://ads.google.com)**
2. Sign in to your **Manager Account** (MCC)
3. Your **Customer ID** is displayed in the top right, formatted as `XXX-XXX-XXXX`
4. **Copy it** → this is your `GOOGLE_ADS_LOGIN_CUSTOMER_ID`

> 💡 The Login Customer ID is only needed if you're using an MCC to manage multiple accounts. If you're managing a single account directly, you can leave this blank.

#### Step 1A-5: Verify Your Credentials

Create a test file to verify everything works:

```python
from google.ads.googleads.client import GoogleAdsClient

client = GoogleAdsClient.load_from_dict({
    "developer_token": "YOUR_DEVELOPER_TOKEN",
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "refresh_token": "YOUR_REFRESH_TOKEN",
    "login_customer_id": "YOUR_MCC_ID_NO_DASHES",
    "use_proto_plus": True
})

# Test: list accessible accounts
ga_service = client.get_service("GoogleAdsService")
customer_service = client.get_service("CustomerService")
accessible = customer_service.list_accessible_customers()
print("Accessible accounts:", accessible.resource_names)
```

If this prints account resource names, your Google Ads credentials are working.

---

### 1B: Cloudinary Credentials

Cloudinary handles all image/video processing — resizing, AI generative fill, platform-specific formatting.

1. Go to **[Cloudinary Sign Up](https://cloudinary.com/users/register_free)** and create a free account
   - Free tier includes 25 credits/month (enough for ~1,000 transformations)
2. After signing up, go to **[Dashboard](https://console.cloudinary.com/pm/getting-started/dashboard)**
3. Your credentials are displayed right on the dashboard:
   - **Cloud Name** → `CLOUDINARY_CLOUD_NAME`
   - **API Key** → `CLOUDINARY_API_KEY`
   - **API Secret** → `CLOUDINARY_API_SECRET` (click "Reveal" to see it)

> 💡 The free tier is generous for development. For production with heavy creative processing, the Plus plan ($89/mo) gives 225 credits.

#### How Cloudinary Connects to the Agent

The **Cloudinary Creative Tools** action (Action #18 on the main agent) and the **Baymax — Creative Innovate** sub-agent both use these credentials. They enable:
- Uploading images/videos from URLs
- Resizing for 20+ platform presets (Instagram, TikTok, YouTube, display ads, etc.)
- AI generative fill for extending images to non-standard aspect ratios
- Batch processing across multiple platforms

---

### 1C: SearchAPI.io Credentials

SearchAPI.io provides real-time Google search results, Google Trends data, and Google Ads Transparency Center access for the Research & Intelligence sub-agent.

1. Go to **[SearchAPI.io Sign Up](https://www.searchapi.io/signup)**
   - Free tier: 100 searches/month
2. After sign up, go to **[Dashboard → API Key](https://www.searchapi.io/dashboard)**
3. **Copy your API key** → `SEARCHAPI_API_KEY`

#### How SearchAPI Connects to the Agent

The **Nemo — Research & Intelligence** uses SearchAPI through three custom actions:
- **Google Search API** — real-time SERP results with ads, organic, knowledge graph
- **Google Ads Transparency Center** — see what ads competitors are running
- **Google Trends Analyzer** — trend data, related queries, geographic interest

These actions pass the API key via `secrets["SEARCHAPI_API_KEY"]` in each action's source code.

---

### 1D: Google AI / Gemini Credentials

The Baymax — Creative Innovate uses Google's Gemini API for AI-powered image generation and vision analysis.

1. Go to **[Google AI Studio](https://aistudio.google.com)**
2. Sign in with your Google account
3. Click **Get API Key** in the left sidebar (or go directly to **[API Keys](https://aistudio.google.com/apikey)**)
4. Click **Create API Key**
   - Select the Google Cloud project you created in Step 1A-2 (or create a new one)
5. **Copy the API key** → `GOOGLE_AI_API_KEY`

> 💡 The free tier provides 15 RPM (requests per minute) for Gemini 2.0 Flash. For production, the pay-as-you-go rate is very affordable.

#### How Gemini Connects to the Agent

The **Baymax — Creative Innovate** sub-agent uses Gemini for:
- AI image generation/extension for social media formats
- Vision analysis of existing creative assets
- Generating display ad variations from source images

The Gemini action file is at `actions/sub-agents/creative-innovate/02_gemini_vision.py`.

---

### Summary: All Credentials

After completing Steps 1A–1D, your `.env` file should look like:

```env
# Google Ads API
GOOGLE_ADS_DEVELOPER_TOKEN=aBcDeFgHiJkLmNoPqR
GOOGLE_ADS_CLIENT_ID=123456789-abcdef.apps.googleusercontent.com
GOOGLE_ADS_CLIENT_SECRET=GOCSPX-AbCdEfGhIjKlMnOpQrStUvWx
GOOGLE_ADS_REFRESH_TOKEN=1//0abCdEfGhIjKl-MnOpQrStUvWxYz_AbCdEfGhIjKlMnO
GOOGLE_ADS_LOGIN_CUSTOMER_ID=123-456-7890

# Cloudinary
CLOUDINARY_CLOUD_NAME=my-cloud-name
CLOUDINARY_API_KEY=123456789012345
CLOUDINARY_API_SECRET=AbCdEfGhIjKlMnOpQrStUvWx

# SearchAPI
SEARCHAPI_API_KEY=abc123def456ghi789

# Google AI (Gemini)
GOOGLE_AI_API_KEY=AIzaSyAbCdEfGhIjKlMnOpQrStUvWxYz
```

---

## Step 2: Create the Main Agent

> These instructions use generic terminology. Adapt button names/menus for your specific agent platform (e.g., OpenAI, or similar).

### 2.1 — Create the Agent Shell

1. On your agent platform, create a new agent with these settings:

| Setting | Value |
|---------|-------|
| Name | `Google Ads API Agent` |
| Model | `claude-opus-4-5` (Anthropic) |
| Access | Private |

2. **Set the Description:**

```
Google Ads strategist with LIVE API access and CONTEXT. Now with FULL CAMPAIGN
support: Create campaigns, ad groups, keywords, manage bidding strategies, PMax,
ad schedules, and location targeting. Features automatic data offloading, memory
checkpoints, and creative assets via Cloudinary.
```

### 2.2 — Paste the System Prompt

1. Open the file: `prompts/main_agent_system_prompt.md`
2. Copy the **entire contents**
3. Paste into the system prompt / instructions field of your agent
4. Save

### 2.3 — Enable Builtin Tools

Enable these 10 builtin tools (names may vary by platform):

- [x] Code Interpreter
- [x] Web Search (Google)
- [x] Researcher
- [x] Todo / Task List
- [x] Web Scraper
- [x] Query Executor (SQL)
- [x] CSV Reader
- [x] String Matcher
- [x] Display File
- [x] File Search

---

## Step 3: Install Custom Actions (28 total)

Each custom action is a Python file that gets pasted into your agent platform's custom action builder. You'll need to:

1. Create the action
2. Paste the source code
3. Configure the credentials (secrets)

### Understanding Credential Patterns

There are 4 credential patterns. Know which one each action uses before you start:

| Pattern | # of Secrets | Actions Using It |
|---------|-------------|-----------------|
| **A** (5-key Google Ads) | 5 | 12 actions — includes `LOGIN_CUSTOMER_ID` as a secret |
| **B** (4-key Google Ads) | 4 | 13 actions — passes `login_customer_id` as a function param |
| **C** (3-key Cloudinary) | 3 | 1 action — Cloudinary Creative Tools |
| **D** (No credentials) | 0 | 3 actions — Package Installer, Session Manager, Reconstruction Doc |

See [Credential Patterns Reference](#credential-patterns-reference) for full details.

### Action-by-Action Installation

For **every action** below, follow this process:

```
1. Create New Custom Action on your platform
2. Set the Name (from table below)
3. Set the Integration type (google_ads, default, or none)
4. Paste the source code from the file path listed
5. Add credential secrets matching the pattern letter
6. Save and verify
```

#### Pattern A Actions (5-key Google Ads) — 12 actions

For each, add these 5 secrets:

| Secret Key | Value from .env |
|------------|----------------|
| `GOOGLE_ADS_DEVELOPER_TOKEN` | Your developer token |
| `GOOGLE_ADS_CLIENT_ID` | Your OAuth2 client ID |
| `GOOGLE_ADS_CLIENT_SECRET` | Your OAuth2 client secret |
| `GOOGLE_ADS_REFRESH_TOKEN` | Your refresh token |
| `GOOGLE_ADS_LOGIN_CUSTOMER_ID` | Your MCC customer ID |

| # | Action Name | Source File |
|---|-------------|------------|
| 1 | Label Manager | `actions/main-agent/01_label_manager.py` |
| 2 | Conversion Tracking Manager | `actions/main-agent/02_conversion_tracking_manager.py` |
| 12 | Scripts Manager | `actions/main-agent/12_scripts_manager.py` |
| 13 | Experiments Manager | `actions/main-agent/13_experiments_manager.py` |
| 19 | Query Planner & Budget Manager | `actions/main-agent/19_query_planner.py` |
| 20 | Recommendations Manager | `actions/main-agent/20_recommendations_manager.py` |
| 23 | Device Performance Manager | `actions/main-agent/23_device_performance_manager.py` |
| 24 | Change History Manager | `actions/main-agent/24_change_history_manager.py` |
| 25 | Campaign Creator | `actions/main-agent/25_campaign_creator.py` |
| 26 | Ad Schedule Manager | `actions/main-agent/26_ad_schedule_manager.py` |
| 27 | Bidding Strategy Manager | `actions/main-agent/27_bidding_strategy_manager.py` |
| 28 | PMax Asset Group Manager | `actions/main-agent/28_pmax_asset_group_manager.py` |

#### Pattern B Actions (4-key Google Ads) — 13 actions

For each, add these 4 secrets:

| Secret Key | Value from .env |
|------------|----------------|
| `DEVELOPER_TOKEN` | Your developer token |
| `CLIENT_ID` | Your OAuth2 client ID |
| `CLIENT_SECRET` | Your OAuth2 client secret |
| `REFRESH_TOKEN` | Your refresh token |

> ⚠️ Note: The **key names** are different from Pattern A (no `GOOGLE_ADS_` prefix). This is by design — these actions accept `login_customer_id` as a function parameter instead.

| # | Action Name | Source File |
|---|-------------|------------|
| 3 | Audience Manager | `actions/main-agent/03_audience_manager.py` |
| 4 | Asset Manager | `actions/main-agent/04_asset_manager.py` |
| 5 | Budget Manager | `actions/main-agent/05_budget_manager.py` |
| 6 | RSA Ad Manager | `actions/main-agent/06_rsa_ad_manager.py` |
| 7 | Bid & Keyword Manager | `actions/main-agent/07_bid_keyword_manager.py` |
| 8 | Negative Keywords Manager | `actions/main-agent/08_negative_keywords_manager.py` |
| 9 | Campaign & Ad Group Manager | `actions/main-agent/09_campaign_adgroup_manager.py` |
| 10 | Google Ads Mutate | `actions/main-agent/10_google_ads_mutate.py` |
| 11 | Account Access Checker | `actions/main-agent/11_account_access_checker.py` |
| 15 | Check User Access Levels | `actions/main-agent/15_check_user_access.py` |
| 16 | API Gateway - Context Manager | `actions/main-agent/16_api_gateway.py` |
| 21 | Search Term Manager | `actions/main-agent/21_search_term_manager.py` |
| 22 | Geo & Location Targeting Manager | `actions/main-agent/22_geo_location_manager.py` |

#### Pattern C Action (3-key Cloudinary) — 1 action

| Secret Key | Value from .env |
|------------|----------------|
| `CLOUDINARY_CLOUD_NAME` | Your Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | Your Cloudinary API key |
| `CLOUDINARY_API_SECRET` | Your Cloudinary API secret |

| # | Action Name | Source File |
|---|-------------|------------|
| 18 | Cloudinary Creative Tools | `actions/main-agent/18_cloudinary_creative_tools.py` |

#### Pattern D Actions (No Credentials) — 3 actions

Just paste the code — no secrets needed.

| # | Action Name | Source File |
|---|-------------|------------|
| 14 | Package Installer | `actions/main-agent/14_package_installer.py` |
| 17 | Session & State Manager | `actions/main-agent/17_session_state_manager.py` |

> 📌 **Tip:** If your platform supports importing actions in bulk, use `configs/agent_registry.json` as the source of truth for IDs, names, and credential patterns.

---

## Step 4: Create Sub-Agents (6 total)

Each sub-agent is a separate agent that the main agent delegates tasks to. They each have their own system prompt, tools, and custom actions.

### Sub-Agent 1: Reporting & Analysis

| Setting | Value |
|---------|-------|
| Name | `Simba — Reporting & Analysis` |
| Model | `claude-opus-4-5` |
| Access | CHAT_ONLY |
| System Prompt | `prompts/sub-agents/01_reporting_analysis.md` |

**Custom Actions (8):** Install from `actions/sub-agents/reporting/`

| # | Action | Source File | Credentials |
|---|--------|-----------|-------------|
| 1 | Performance Reporter | `01_performance_reporter.py` | 4-key Google Ads (Pattern B) |
| 2 | Search Terms Analyzer | `02_search_terms_analyzer.py` | 4-key Google Ads (Pattern B) |
| 3 | Interactive Keyword Viewer | `03_interactive_keyword_viewer.py` | 4-key Google Ads (Pattern B) |
| 4 | Interactive Ad Viewer | `04_interactive_ad_viewer.py` | 4-key Google Ads (Pattern B) |
| 5 | Auction Insights Reporter | `05_auction_insights_reporter.py` | 4-key Google Ads (Pattern B) |
| 6 | Change History Auditor | `06_change_history_auditor.py` | 4-key Google Ads (Pattern B) |
| 7 | PMax Enhanced Reporting | `07_pmax_enhanced_reporting.py` | 4-key Google Ads (Pattern B) |
| 8 | Package Installer | `08_package_installer.py` | None (Pattern D) |

**Builtin Tools (9):** code_interpreter, query_executor, csv_reader, string_matcher, display_file, file_search, browser_use, researcher, google_web_search

> ⚠️ Actions 3 & 4 (Interactive Keyword/Ad Viewers) use Google Ads API **v18** while the others use **v19**. Verify the `google-ads` pip package supports both.

---

### Sub-Agent 2: Research & Intelligence

| Setting | Value |
|---------|-------|
| Name | `Nemo — Research & Intelligence` |
| Model | `claude-opus-4-5` |
| Access | CHAT_ONLY |
| System Prompt | `prompts/sub-agents/02_research_intelligence.md` |

**Custom Actions (4+1):** Install from `actions/sub-agents/research/`

| # | Action | Source File | Credentials |
|---|--------|-----------|-------------|
| 1 | Keyword Planner | `01_keyword_planner.py` | 4-key Google Ads (Pattern B) |
| 2 | Google Search API | `02_google_search_api.py` | 1 secret: `SEARCHAPI_API_KEY` |
| 3 | Ads Transparency Center | `03_ads_transparency_center.py` | 1 secret: `SEARCHAPI_API_KEY` |
| 4 | Google Trends Analyzer | `04_google_trends_analyzer.py` | 1 secret: `SEARCHAPI_API_KEY` |
| 5 | Package Installer | *(reuse from main agent)* | None (Pattern D) |

**Builtin Tools (10):** code_interpreter, query_executor, csv_reader, string_matcher, display_file, file_search, browser_use, researcher, google_web_search, web_scraper

---

### Sub-Agent 3: Optimization

| Setting | Value |
|---------|-------|
| Name | `Elsa — Optimization` |
| Model | `claude-opus-4-5` |
| Access | CHAT_ONLY |
| System Prompt | `prompts/sub-agents/03_optimization.md` |

**Custom Actions:** ⚠️ **NONE EXIST YET**

This sub-agent's system prompt references two custom actions that need to be built:
- **Recommendations Manager - API** — `list`, `apply`, `dismiss`, `get_score`
- **Bulk Operations Manager - API** — `bulk_pause`, `bulk_enable`, `bulk_bid_change`, `bulk_budget_change`, `export`

> 🔧 **TODO:** Build these actions using the Google Ads API. The parameter signatures are documented in the system prompt file. Both would use Pattern B (4-key Google Ads) credentials.

**Builtin Tools (10):** code_interpreter, query_executor, csv_reader, string_matcher, display_file, file_search, browser_use, researcher, google_web_search, web_scraper

---

### Sub-Agent 4: Shopping & PMax

| Setting | Value |
|---------|-------|
| Name | `Aladdin — Shopping & PMax` |
| Model | `claude-opus-4-5` |
| Access | CHAT_ONLY |
| System Prompt | `prompts/sub-agents/04_shopping_pmax.md` |

**Custom Actions:** ⚠️ **NONE EXIST YET**

This sub-agent's system prompt references one custom action that needs to be built:
- **Shopping & PMax Manager - API** — `list_shopping`, `list_pmax`, `list_asset_groups`, `get_product_performance`, `get_pmax_performance`, `get_pmax_insights`, `pause_asset_group`, `enable_asset_group`

> 🔧 **TODO:** Build this action using the Google Ads API (`google-ads` Python SDK). Would use Pattern B credentials. The main agent's PMax Asset Group Manager (Action #28) covers some of this functionality and can serve as a starting template.

**Builtin Tools (10):** code_interpreter, query_executor, csv_reader, string_matcher, display_file, file_search, browser_use, researcher, google_web_search, web_scraper

---

### Sub-Agent 5: Creative

| Setting | Value |
|---------|-------|
| Name | `Moana — Creative` |
| Model | `claude-opus-4-5` |
| Access | CHAT_ONLY |
| System Prompt | `prompts/sub-agents/05_creative.md` |

**Custom Actions (2):** Install from `actions/sub-agents/creative/`

| # | Action | Source File | Credentials |
|---|--------|-----------|-------------|
| 1 | Responsive Display Ads Manager | `01_responsive_display_ads_manager.py` | 4-key Google Ads (Pattern B) |
| 2 | Demand Gen Ads Manager | `02_demand_gen_ads_manager.py` | 4-key Google Ads (Pattern B) |

**Builtin Tools (10):** code_interpreter, query_executor, csv_reader, string_matcher, display_file, file_search, browser_use, google_web_search, researcher, web_scraper

---

### Sub-Agent 6: Baymax — Creative Innovate

| Setting | Value |
|---------|-------|
| Name | `Baymax — Creative Innovate` |
| Model | `claude-sonnet-4-5` ⚡ *(lighter model — intentional)* |
| Access | CHAT_ONLY |
| System Prompt | `prompts/sub-agents/06_creative_innovate.md` |

**Custom Actions (2+1):** Install from `actions/sub-agents/creative-innovate/`

| # | Action | Source File | Credentials |
|---|--------|-----------|-------------|
| 1 | Cloudinary Tools | `01_cloudinary_tools.py` | 3-key Cloudinary (Pattern C) |
| 2 | Gemini Vision | `02_gemini_vision.py` | 1 secret: `GOOGLE_AI_API_KEY` |
| 3 | Package Installer | *(reuse from main agent)* | None (Pattern D) |

---

## Step 5: Link Sub-Agents to Main Agent

After creating all 6 sub-agents, you need to register them with the main agent so it can delegate tasks.

1. Go to the **Main Agent** settings
2. Find the **Sub-Agents** section
3. Add each sub-agent by searching for its name or ID:

| # | Sub-Agent Name | Agent ID |
|---|----------------|----------|
| 1 | Simba — Reporting & Analysis | `8b9991fd-7750-417e-a2c2-69527d64388b` |
| 2 | Nemo — Research & Intelligence | `47885bdc-0390-44a4-ab58-9046c1182691` |
| 3 | Elsa — Optimization | `c08c6cde-b9a6-4aa4-b7a2-3b6ed5720cbb` |
| 4 | Aladdin — Shopping & PMax | `b57147ce-fa6e-47ec-b92b-39bc8d16d7a7` |
| 5 | Moana — Creative | `9aeb9afc-bd87-4df7-955a-1b928b23aa0e` |
| 6 | Baymax — Creative Innovate | `9b971c1c-0204-4496-869e-7a3620718242` |

> 💡 Note: Agent IDs will be **different** if you're creating new agents (they're auto-generated). The IDs above are from the original build and are provided for reference.

The main agent's system prompt includes the **Sub-Agent Delegation Protocol** that tells it when to handle tasks directly vs. delegate. The **Session & State Manager** (Action #17) coordinates handoffs.

---

## Step 6: Grant User Access

If you need to share the agent with team members:

1. Go to Main Agent settings → **Sharing / Access**
2. Add users with **CAN_EDIT** permission
3. They'll be able to use and modify the agent

---

## Step 7: Validation & Testing

Run these tests in order to verify the full system is working:

### Test 1: Package Installation

```
You: "Install the google-ads package"
Expected: Agent runs code_interpreter to pip install google-ads>=28.1.0
```

### Test 2: Account Connection

```
You: "Test my Google Ads connection"
Expected: Agent uses Account Access Checker → test_connection
         Shows list of accessible accounts
```

### Test 3: Account Summary

```
You: "Show me an account summary for [YOUR ACCOUNT NAME]"
Expected: Agent uses Query Planner → get_account_summary
         Shows total spend, conversions, entity counts
```

### Test 4: Read Operation

```
You: "List the top 5 campaigns by spend for [YOUR ACCOUNT NAME]"
Expected: Agent uses Campaign Manager → list_campaigns with cost filter
         Shows campaigns in a table with dollar amounts
```

### Test 5: Write Operation (Safe)

```
You: "Create a test label called 'Agent Test' with color blue"
Expected: Agent uses Label Manager → create_label
         Shows preview, asks for CONFIRM before creating
```

### Test 6: Sub-Agent Delegation

```
You: "Give me a full performance report for all campaigns in [ACCOUNT] for the last 30 days"
Expected: Agent delegates to Reporting sub-agent
         Returns summarized findings, not a data dump
```

### Test 7: Cloudinary

```
You: "Upload this image and resize it for Instagram: [IMAGE_URL]"
Expected: Agent uses Cloudinary Creative Tools or delegates to Baymax — Creative Innovate
         Returns resized image URLs
```

---

## Credential Patterns Reference

### Pattern A: 5-Key Google Ads

Used by **12 actions** where the MCC Login Customer ID is stored as a secret.

```
GOOGLE_ADS_DEVELOPER_TOKEN  → Developer token from Google Ads API Center
GOOGLE_ADS_CLIENT_ID        → OAuth2 client ID from Google Cloud Console
GOOGLE_ADS_CLIENT_SECRET    → OAuth2 client secret from Google Cloud Console
GOOGLE_ADS_REFRESH_TOKEN    → OAuth2 refresh token (generated once)
GOOGLE_ADS_LOGIN_CUSTOMER_ID → MCC account ID (XXX-XXX-XXXX format)
```

### Pattern B: 4-Key Google Ads

Used by **13 actions** where Login Customer ID is passed as a function parameter.

```
DEVELOPER_TOKEN  → Same developer token, different key name
CLIENT_ID        → Same OAuth2 client ID, different key name
CLIENT_SECRET    → Same OAuth2 client secret, different key name
REFRESH_TOKEN    → Same refresh token, different key name
```

> ⚠️ The **values** are identical to Pattern A. Only the **key names** differ. This is because some actions were written with different naming conventions. The underlying credentials are the same.

### Pattern C: 3-Key Cloudinary

```
CLOUDINARY_CLOUD_NAME  → From Cloudinary Dashboard
CLOUDINARY_API_KEY     → From Cloudinary Dashboard
CLOUDINARY_API_SECRET  → From Cloudinary Dashboard (click Reveal)
```

### Pattern D: No Credentials

Actions that don't call external APIs: Package Installer, Session & State Manager.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    GOOGLE ADS AGENT (Main)                          │
│                    claude-opus-4-5 · PRIVATE                        │
│                    28 Custom Actions · 10 Builtin Tools             │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ Filter-First │  │    CEP       │  │  Session & State Manager │  │
│  │ Architecture │  │  Protocol    │  │  (Coordination Bus)      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │ Delegates via handoff protocol
          ┌──────────┬───────┼───────┬──────────┬──────────┐
          │          │       │       │          │          │
     ┌────┴───┐ ┌───┴──┐ ┌─┴──┐ ┌──┴───┐ ┌───┴───┐ ┌───┴────────┐
     │Report- │ │Rese- │ │Opt-│ │Shop- │ │Creat- │ │Creative    │
     │ing &   │ │arch &│ │imi-│ │ping &│ │ive    │ │Innovate    │
     │Analysis│ │Intel │ │zat-│ │PMax  │ │       │ │Tool        │
     │[Simba]  │ │[Nemo]│ │ion │ │[Aladdin]│ │[Moana] │ │(Sonnet 4.5)│
     │        │ │      │ │[3] │ │      │ │       │ │            │
     │8 acts  │ │5 acts│ │⚠️0 │ │⚠️0   │ │2 acts │ │3 acts      │
     └────────┘ └──────┘ └────┘ └──────┘ └───────┘ └────────────┘
```

For the full technical architecture with action schemas, parameter signatures, and delegation flow, see **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**.

For the Cloudflare Buddy production architecture (Durable Objects, Vectorize, D1, R2, Agents SDK), see **[docs/BUDDY_ARCHITECTURE.md](docs/BUDDY_ARCHITECTURE.md)**.

### How This Repo Compares to Other AI Agents

| Feature | This Agent | Google Ads Scripts | Microsoft Copilot | Perplexity | Generic Claude |
|---------|-----------|-------------------|-------------------|------------|---------------|
| Live Google Ads API R/W | 28 actions | JS-only scripting | No Ads access | No API | No API |
| Write safety (CEP) | Confirm/Execute/Post | None | N/A | N/A | N/A |
| Multi-provider AI | Claude + GPT + Gemini | N/A | GPT only | Own models | Claude only |
| Sub-agent delegation | 6 specialists | N/A | N/A | N/A | N/A |
| Semantic memory | Vectorize (prod) | None | Limited | Built-in | Conversation only |
| Self-deployable | 3 paths | Script editor | SaaS only | SaaS only | API only |

---

## Known Issues

| Issue | Severity | Details | Workaround |
|-------|----------|---------|------------|
| **Optimization sub-agent has no actions** | 🔴 Critical | System prompt describes Recommendations Manager & Bulk Operations Manager, but neither action exists | Build them using Google Ads API, or use main agent's Recommendations Manager (#20) directly |
| **Shopping & PMax sub-agent has no actions** | 🔴 Critical | System prompt describes Shopping & PMax Manager, but no action exists | Build it, or use main agent's PMax Asset Group Manager (#28) as a starting point |
| **API version mismatch in Reporting** | 🟡 Medium | Interactive Keyword/Ad Viewers use v18, other reporting actions use v19 | Verify `google-ads` pip package handles both; consider upgrading v18 actions |
| **Pattern A vs B naming inconsistency** | 🟡 Low | Same credentials stored under different key names across actions | Just enter the same values — works fine, just confusing during setup |

---

## Troubleshooting

### "No account found matching..."

The `resolve_customer_id()` function searches for accounts under your MCC. Make sure:
- Your `LOGIN_CUSTOMER_ID` is the MCC (Manager) account, not a child account
- The account you're searching for is linked to your MCC
- The search string matches part of the account's descriptive name

### "google-ads package not found"

The system prompt instructs the agent to run `pip install google-ads>=28.1.0` at the start of every conversation. If it's failing:
- Make sure `code_interpreter` is enabled
- Try running the install manually in the first message

### "OAuth credentials expired"

Refresh tokens generally don't expire, but they can be revoked if:
- You changed your Google account password
- You removed the app's access in [Google Security Settings](https://myaccount.google.com/permissions)
- The token hasn't been used in 6+ months

**Fix:** Re-run the refresh token generation from Step 1A-3.

### "Developer token not approved"

If your developer token is in "Test Account" mode:
- It only works with [Google Ads test accounts](https://developers.google.com/google-ads/api/docs/first-call/test-accounts)
- Apply for Basic Access at [Google Ads API Center](https://ads.google.com/aw/apicenter)
- Approval typically takes 1-3 business days

### "Rate limit exceeded"

Google Ads API has these limits:
- **Basic Access:** 15,000 operations/day, 4 requests/second
- **Standard Access:** Unlimited operations, 100 requests/second

If hitting limits, the system's Filter-First Architecture should help — use `cost_min`, `status`, and `limit` params to reduce result sets.

### Sub-agent not responding

- Verify the sub-agent is linked in the main agent's sub-agents list
- Check that the Session & State Manager action (#17) is installed
- Ensure the sub-agent has its own credentials configured (they don't share with the main agent)

---

## Security

See [`SECURITY.md`](SECURITY.md) for:
- Vulnerability reporting process
- CORS, rate limiting, and input validation practices
- Credential management guidelines
- Write safety protocol (CEP: Confirm → Execute → Post-check)

Key security features in v2.0:
- **No wildcard CORS** — server defaults to localhost; configure via `ALLOWED_ORIGINS`
- **Rate limiting** — 30 req/min per IP (configurable via `RATE_LIMIT_MAX`)
- **Error sanitization** — generic client errors, full server-side logging
- **GAQL injection prevention** — period values whitelisted
- **No hardcoded secrets** — everything via `.env` / environment variables

---

## License

MIT License. See [`LICENSE`](LICENSE) for full text.

The Google Ads API is subject to Google's [Terms of Service](https://developers.google.com/google-ads/api/docs/terms). Third-party services (Cloudinary, SearchAPI, Stripe) are subject to their respective terms.

---

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the full guide. Priority areas:

1. **Optimization sub-agent actions** — system prompt exists, needs API actions built
2. **Shopping & PMax sub-agent actions** — same as above
3. **Test coverage** — unit tests for the deploy package
4. **Semantic memory** — port Vectorize memory from Buddy to Python (pgvector/Pinecone)
5. **Streaming responses** — add SSE endpoint for real-time tool execution

```bash
# Quick contributor setup
git clone https://github.com/itallstartedwithaidea/google-ads-api-agent.git
cd google-ads-api-agent
python -m venv venv && source venv/bin/activate
pip install -e ".[all]"
cp .env.example .env
python scripts/validate.py
```

---

> **Live at:** [googleadsagent.ai](https://googleadsagent.ai)  
> **Version:** 2.0.0  
> **License:** MIT  
> **Last Updated:** 2026-03-05
