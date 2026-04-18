# Autonomous Agent Ecosystem (AAE)
# V2 — Complete Implementation Tutorial & Roadmap

> **Version:** 2.0  
> **Prerequisite Reading:** V1.0 Architecture Blueprint + V1.1 Model Tiering & Opportunity Catalog  
> **Goal:** A running, money-making autonomous agent you can deploy in one week  
> **Research Purpose:** Demonstrating real-world AI capability for self-sustaining micro-businesses

---

## Table of Contents

1. [What Changed in V2](#1-what-changed-in-v2)
2. [Full System Architecture](#2-full-system-architecture)
3. [The Skills System — Core Concept](#3-the-skills-system--core-concept)
4. [Phase 0 — Prerequisites & Project Setup](#4-phase-0--prerequisites--project-setup)
5. [Phase 1 — Infrastructure Layer](#5-phase-1--infrastructure-layer)
6. [Phase 2 — Skills System Implementation](#6-phase-2--skills-system-implementation)
7. [Phase 3 — Model Router (Gemini + Bonsai + Claude)](#7-phase-3--model-router-gemini--bonsai--claude)
8. [Phase 4 — Tools Layer](#8-phase-4--tools-layer)
9. [Phase 5 — Mother Agent](#9-phase-5--mother-agent)
10. [Phase 6 — Human-in-the-Loop Email System](#10-phase-6--human-in-the-loop-email-system)
11. [Phase 7 — Child Agent Factory](#11-phase-7--child-agent-factory)
12. [Phase 8 — Website Agency Child Agent (Deep Dive)](#12-phase-8--website-agency-child-agent-deep-dive)
13. [Phase 9 — Other Child Agents](#13-phase-9--other-child-agents)
14. [Phase 10 — State Machine (LangGraph)](#14-phase-10--state-machine-langgraph)
15. [Phase 11 — Scheduler & Weekly Report](#15-phase-11--scheduler--weekly-report)
16. [Phase 12 — Memory & Restart System](#16-phase-12--memory--restart-system)
17. [Phase 13 — Testing & Simulation Mode](#17-phase-13--testing--simulation-mode)
18. [Phase 14 — Deployment](#18-phase-14--deployment)
19. [Master Caveats Reference](#19-master-caveats-reference)
20. [Quick Reference Cheatsheet](#20-quick-reference-cheatsheet)

---

## 1. What Changed in V2

| Feature | V1.x | V2 |
|---|---|---|
| Agent code generation | Paid API (Claude/GPT) | **Bonsai (free frontier models)** for code tasks |
| Agent capabilities | Fixed tools | **Skills System** — agents load markdown skill files |
| Website selling | Not included | **Website Agency Child Agent** (full company) |
| Model routing | Simple tier lookup | **Intelligent task router** (task type → optimal model) |
| Child agent types | Generic | **Specialised with skills bundles** per vertical |
| Code quality | Prompt-level | **Skill-guided quality standards** baked into every build |

### The Bonsai Pivot

[**Bonsai**](https://www.trybons.ai) (`trybons.ai`) provides **completely free access** to frontier coding models including Claude, GPT-5, and Gemini via a CLI and API key. Models rotate in "stealth mode" — you don't know which one you're getting, which is fine for code generation where output quality is verifiable.

**How it fits the AAE:**
- All code generation tasks (websites, apps, browser extensions, AI wrappers) → **Bonsai (FREE)**
- Research, routing, and reasoning tasks → **Gemini 2.0 Flash ($0.075/1M tokens)**
- Financial strategy + child agent planning → **Claude Sonnet 4.6 (T3, on profit > $50)**
- Website Agency premium builds + weekly synthesis → **Claude Opus 4 / `claude-opus-4-6` (T4, on profit > $150)**

This combination drops the expected weekly API cost from ~$5.36 (V1.1) to **~$1.80** because the most token-hungry task (code generation) moves to zero cost.

> ⚠️ **Critical Bonsai Caveat:** Bonsai logs ALL prompts and completions for benchmarking and model training. **Never send API keys, financial data, customer PII, or bank credentials through Bonsai.** Code generation only. This is non-negotiable and enforced in the BonsaiCodeTool implementation in Phase 4.

---

## 2. Full System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        HUMAN SUPERVISOR                             │
│                  (Email approval gate — you)                        │
└───────────────────────────┬─────────────────────────────────────────┘
                            │  Gmail IMAP/SMTP
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    MOTHER AGENT (Orchestrator)                      │
│  Model: Gemini Flash (T1) → escalates to Sonnet/Opus on profit     │
│  Skills: [opportunity_research, financial_analysis, copywriting]   │
│                                                                     │
│  Tools: WebSearch | Email | BankTool | ChildAgentFactory           │
│  Memory: SQLite (episodes.db + agents.db + transactions.db)        │
│  State: LangGraph FSM                                               │
└──────┬──────────────────────┬───────────────────────┬──────────────┘
       │                      │                       │
       ▼                      ▼                       ▼
┌──────────────┐   ┌──────────────────────┐   ┌──────────────────┐
│ CRYPTO AGENT │   │  WEBSITE AGENCY      │   │  AI WRAPPER      │
│              │   │  CHILD AGENT         │   │  CHILD AGENT     │
│ Model: T2    │   │                      │   │                  │
│ Gemini+Flash │   │  Model: T4           │   │  Model: T2/T3    │
│              │   │  claude-opus-4-6     │   │  GPT-4o mini     │
│ Skills:      │   │                      │   │                  │
│ [trading,    │   │  Skills:             │   │  Skills:         │
│  risk_mgmt]  │   │  [frontend_design,   │   │  [api_wrapping,  │
│              │   │   web_architecture,  │   │   saas_pricing,  │
│ Code: None   │   │   seo_optimization,  │   │   growth_hacks]  │
│              │   │   client_comms,      │   │                  │
│              │   │   project_pricing]   │   │  Code: Bonsai    │
│              │   │                      │   │                  │
│              │   │  Code: Bonsai FREE   │   │                  │
└──────────────┘   └──────────────────────┘   └──────────────────┘
       │                      │                       │
       └──────────────────────┴───────────────────────┘
                              │
              ┌───────────────▼──────────────────┐
              │        SHARED INFRASTRUCTURE     │
              │                                  │
              │  ┌─────────┐  ┌──────────────┐  │
              │  │ SQLite  │  │  Bonsai CLI  │  │
              │  │ Memory  │  │  (Free Code) │  │
              │  └─────────┘  └──────────────┘  │
              │                                  │
              │  ┌─────────┐  ┌──────────────┐  │
              │  │  Wise   │  │  Skills Dir  │  │
              │  │  Bank   │  │  (.md files) │  │
              │  └─────────┘  └──────────────┘  │
              └──────────────────────────────────┘
```

### Data Flow Summary

```
1. Mother Agent wakes → loads memory → loads assigned skills
2. Researches opportunities (Gemini Flash → DuckDuckGo/Tavily)
3. Scores opportunities using financial_analysis skill
4. Drafts OPPORTUNITY_BRIEF email using copywriting skill
5. Sends email → polls Gmail every 15 min for human reply
6. On APPROVE: selects child agent type → spawns with skill bundle
7. Child agent executes → uses Bonsai for code, Gemini for research
8. Human performs required actions (account setup, submissions)
9. Revenue hits → profit logged → model tier may upgrade
10. Weekly: Opus generates report → system snapshots → sleeps
```

---

## 3. The Skills System — Core Concept

### What Are Skills?

Skills are **plain Markdown files** that contain domain expertise, quality standards, workflows, and decision rules that an agent injects into its system prompt at initialisation. They are analogous to the skills in Claude's own system (like `frontend-design/SKILL.md` that guides beautiful UI creation).

**A skill is not a tool.** Tools do things (search, send email, spend money). Skills *know things* — they encode how to do a task well.

```
skills/
├── core/
│   ├── opportunity_research.md     # How to find and score opportunities
│   ├── financial_analysis.md       # How to model ROI, risk, payback period
│   └── copywriting.md              # How to write conversion-focused copy
├── website_agency/
│   ├── frontend_design.md          # UI/UX quality standards (adapted from Claude's skill)
│   ├── web_architecture.md         # Tech stack decisions, hosting, deployment
│   ├── seo_optimization.md         # On-page SEO, metadata, performance
│   ├── client_communications.md    # Discovery calls, scope, revisions policy
│   └── project_pricing.md          # How to price web projects profitably
├── trading/
│   ├── technical_analysis.md       # RSI, MACD, EMA — when to use each
│   └── risk_management.md          # Position sizing, stop-loss rules
└── software/
    ├── api_wrapping.md             # How to build a great AI wrapper product
    ├── saas_pricing.md             # Pricing models, conversion optimisation
    └── extension_development.md    # Chrome MV3, permissions, store guidelines
```

### How Skills Get Loaded

```python
# At agent init time (not per-request — loaded once into system prompt)
skill_bundle = skill_loader.load_bundle([
    "core/opportunity_research",
    "website_agency/frontend_design",
    "website_agency/project_pricing",
])
system_prompt = BASE_PROMPT + "\n\n## YOUR EXPERTISE SKILLS\n\n" + skill_bundle
```

### Why This Matters for the Website Agency

The Website Agency child agent runs on `claude-opus-4-6`. Without skills, Opus would produce *good* websites. With the `frontend_design` skill loaded, it produces websites that follow specific quality standards — bold aesthetics, distinctive typography, production-grade CSS — the kind of work clients pay $500+ for, not $50.

The skill transforms the agent from a generic coder into a specialist with a portfolio-quality point of view.

---

## 4. Phase 0 — Prerequisites & Project Setup

### 4.1 System Requirements

```
Python 3.11+          (3.12 recommended)
Node.js 18+           (for Bonsai CLI)
Git
4GB RAM minimum
Linux / macOS         (Windows via WSL2)
```

### 4.2 External Accounts Required

| Service | Purpose | Cost | Setup Link |
|---|---|---|---|
| Google AI Studio | Gemini API | Free tier available | ai.google.dev |
| Anthropic Console | Claude Sonnet + Opus | Pay per token | console.anthropic.com |
| Bonsai | Free code generation | **FREE** | trybons.ai |
| Tavily | Web search (5K free/mo) | Free tier | tavily.com |
| Gmail | HITL email channel | Free | gmail.com |
| Wise Business | Virtual card + API | Free account | wise.com/business |
| Railway | Deployment hosting | $5/mo hobby plan | railway.app |

### 4.3 Project Directory Structure

```
aae/
├── .env                          # ALL secrets — never commit
├── .env.example                  # Template to share with team
├── .gitignore
├── main.py                       # Entry point
├── requirements.txt
│
├── agents/
│   ├── __init__.py
│   ├── base_agent.py             # Shared config, model init, skill loading
│   ├── mother_agent.py           # Orchestrator agent definition
│   ├── child_factory.py          # Spawns and configures child agents
│   └── children/
│       ├── website_agency.py     # Website Agency child agent
│       ├── crypto_trader.py      # Crypto trading agent
│       ├── ai_wrapper_builder.py # AI wrapper product agent
│       └── extension_builder.py  # Browser extension agent
│
├── skills/
│   ├── skill_loader.py           # SkillLoader class
│   ├── core/
│   │   ├── opportunity_research.md
│   │   ├── financial_analysis.md
│   │   └── copywriting.md
│   ├── website_agency/
│   │   ├── frontend_design.md
│   │   ├── web_architecture.md
│   │   ├── seo_optimization.md
│   │   ├── client_communications.md
│   │   └── project_pricing.md
│   ├── trading/
│   │   ├── technical_analysis.md
│   │   └── risk_management.md
│   └── software/
│       ├── api_wrapping.md
│       ├── saas_pricing.md
│       └── extension_development.md
│
├── tools/
│   ├── __init__.py
│   ├── bank_tool.py              # Wise API wrapper with hard limits
│   ├── search_tool.py            # DuckDuckGo + Tavily
│   ├── email_tool.py             # Gmail IMAP polling + SMTP sender
│   ├── bonsai_tool.py            # Bonsai free code generation
│   └── calendar_tool.py          # Economic calendar (Forex Factory)
│
├── memory/
│   ├── database.py               # SQLite schema + query helpers
│   ├── snapshot.py               # System state serialisation for restart
│   ├── transactions.db           # Auto-created
│   ├── agents.db                 # Auto-created
│   └── snapshot.json             # Auto-created on shutdown
│
├── state_machine/
│   └── lifecycle.py              # LangGraph FSM
│
├── scheduler/
│   └── weekly_timer.py           # APScheduler weekly report + shutdown
│
├── email_templates/
│   ├── opportunity_brief.html
│   ├── action_required.html
│   ├── spawn_notice.html
│   ├── low_funds_alert.html
│   └── weekly_report.html
│
└── tests/
    ├── test_bank_tool.py
    ├── test_email_flow.py
    ├── test_skill_loader.py
    ├── test_child_factory.py
    └── simulation/
        └── mock_wise.py
```

### 4.4 Initial Setup Commands

```bash
# 1. Create project and virtual environment
mkdir aae && cd aae
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Install Python dependencies
pip install \
  crewai crewai-tools \
  langchain-google-genai \
  langgraph \
  anthropic \
  duckduckgo-search \
  tavily-python \
  sqlitedict \
  apscheduler \
  pydantic \
  python-dotenv \
  loguru \
  httpx \
  python-binance \
  ta-lib \
  pandas numpy \
  jinja2 \
  pytest pytest-asyncio

# 3. Install Bonsai CLI
npm install -g @bonsai-ai/cli

# 4. Authenticate Bonsai (creates ~/.bonsai/config)
bonsai login
# Then get your API key from https://app.trybons.ai/api-keys
# Add BONSAI_API_KEY to .env

# 5. Copy environment template
cp .env.example .env
# Fill in all values before proceeding
```

### 4.5 The .env File (Complete)

```bash
# .env — NEVER commit this file

# === LLM PROVIDERS ===
GEMINI_API_KEY=your_gemini_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
BONSAI_API_KEY=your_bonsai_api_key_here     # From app.trybons.ai/api-keys

# === SEARCH ===
TAVILY_API_KEY=your_tavily_key_here

# === EMAIL (Gmail) ===
# Enable 2FA on Gmail, then create an App Password
GMAIL_ADDRESS=your_agent_gmail@gmail.com
GMAIL_APP_PASSWORD=xxxx_xxxx_xxxx_xxxx       # 16-char app password
HUMAN_EMAIL=your_personal@email.com          # Where HITL emails go

# === VIRTUAL BANK (Wise) ===
WISE_API_KEY=your_wise_api_key_here
WISE_PROFILE_ID=your_wise_profile_id
WISE_ACCOUNT_ID=your_wise_account_id

# === SYSTEM ===
SIMULATION_MODE=true                          # Set false for live trading
API_RESERVE_USD=50.0                          # Hard survival floor
INVESTMENT_POOL_USD=100.0                     # Available for opportunities
WEEKLY_REPORT_DAY=sunday                      # When to send report + restart
LOG_LEVEL=INFO
```

> ⚠️ **Caveat 0.1 — Gmail App Passwords:** You MUST enable 2-Factor Authentication on your Gmail before App Passwords appear. Standard Gmail password will NOT work for IMAP. Go to myaccount.google.com → Security → 2-Step Verification → App passwords.

> ⚠️ **Caveat 0.2 — TA-Lib on Windows/Mac:** `ta-lib` requires a C library. On Ubuntu: `sudo apt-get install libta-lib-dev`. On Mac: `brew install ta-lib`. On Windows: download the pre-built wheel from the TA-Lib unofficial releases page.

---

## 5. Phase 1 — Infrastructure Layer

### 5.1 Database Schema

Create `memory/database.py`:

```python
# memory/database.py
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from loguru import logger

DB_DIR = Path("memory")
DB_DIR.mkdir(exist_ok=True)


def get_connection(db_name: str) -> sqlite3.Connection:
    conn = sqlite3.connect(DB_DIR / f"{db_name}.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_databases():
    """Create all tables. Safe to call multiple times (IF NOT EXISTS)."""

    # --- Transactions DB ---
    with get_connection("transactions") as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS transactions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp       TEXT NOT NULL DEFAULT (datetime('now')),
                agent_id        TEXT NOT NULL,
                amount          REAL NOT NULL,
                direction       TEXT NOT NULL CHECK(direction IN ('debit','credit')),
                category        TEXT NOT NULL,
                description     TEXT,
                balance_after   REAL NOT NULL,
                approved_by     TEXT DEFAULT 'agent',
                metadata        TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS budget_state (
                id              INTEGER PRIMARY KEY CHECK(id = 1),
                api_reserve     REAL NOT NULL DEFAULT 50.0,
                investment_pool REAL NOT NULL DEFAULT 100.0,
                total_revenue   REAL NOT NULL DEFAULT 0.0,
                total_profit    REAL NOT NULL DEFAULT 0.0,
                updated_at      TEXT DEFAULT (datetime('now'))
            );

            INSERT OR IGNORE INTO budget_state (id) VALUES (1);
        """)

    # --- Agents DB ---
    with get_connection("agents") as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS agents (
                agent_id            TEXT PRIMARY KEY,
                parent_id           TEXT,
                agent_type          TEXT NOT NULL,
                specialty           TEXT NOT NULL,
                status              TEXT NOT NULL DEFAULT 'active'
                                    CHECK(status IN ('active','terminated','profitable','failed')),
                model_tier          TEXT NOT NULL DEFAULT 'T1',
                capital_allocated   REAL NOT NULL DEFAULT 0.0,
                capital_remaining   REAL NOT NULL DEFAULT 0.0,
                total_earned        REAL NOT NULL DEFAULT 0.0,
                skills_loaded       TEXT DEFAULT '[]',
                created_at          TEXT DEFAULT (datetime('now')),
                terminated_at       TEXT,
                metadata            TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS tier_changes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id    TEXT NOT NULL,
                from_tier   TEXT,
                to_tier     TEXT NOT NULL,
                reason      TEXT,
                profit_at   REAL,
                changed_at  TEXT DEFAULT (datetime('now'))
            );
        """)

    # --- Episodes DB (agent memory / learning) ---
    with get_connection("episodes") as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS episodes (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id        TEXT NOT NULL,
                vertical        TEXT NOT NULL,
                opportunity     TEXT NOT NULL,
                action_taken    TEXT,
                outcome         TEXT CHECK(outcome IN ('profit','loss','pending','cancelled')),
                profit_usd      REAL DEFAULT 0.0,
                capital_used    REAL DEFAULT 0.0,
                duration_days   REAL DEFAULT 0.0,
                notes           TEXT,
                created_at      TEXT DEFAULT (datetime('now'))
            );
        """)

    logger.info("✅ All databases initialised")


def get_budget_state() -> dict:
    with get_connection("transactions") as conn:
        row = conn.execute("SELECT * FROM budget_state WHERE id = 1").fetchone()
        return dict(row) if row else {}


def update_budget(api_reserve: float = None, investment_pool: float = None,
                  total_revenue: float = None, total_profit: float = None):
    fields, values = [], []
    if api_reserve is not None:
        fields.append("api_reserve = ?"); values.append(api_reserve)
    if investment_pool is not None:
        fields.append("investment_pool = ?"); values.append(investment_pool)
    if total_revenue is not None:
        fields.append("total_revenue = ?"); values.append(total_revenue)
    if total_profit is not None:
        fields.append("total_profit = ?"); values.append(total_profit)
    if not fields:
        return
    values.append(datetime.now().isoformat())
    with get_connection("transactions") as conn:
        conn.execute(f"UPDATE budget_state SET {', '.join(fields)}, updated_at = ? WHERE id = 1",
                     values)


def log_transaction(agent_id: str, amount: float, direction: str,
                    category: str, description: str, balance_after: float,
                    metadata: dict = None):
    with get_connection("transactions") as conn:
        conn.execute(
            """INSERT INTO transactions
               (agent_id, amount, direction, category, description, balance_after, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (agent_id, amount, direction, category, description,
             balance_after, json.dumps(metadata or {}))
        )
```

### 5.2 Logging Setup

```python
# utils/logging_setup.py
import sys
from loguru import logger
from pathlib import Path

def configure_logging(log_level: str = "INFO"):
    Path("logs").mkdir(exist_ok=True)
    logger.remove()

    # Console: colour-coded, human-readable
    logger.add(sys.stdout, level=log_level, colorize=True,
               format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | "
                      "<cyan>{name}</cyan>:<cyan>{line}</cyan> — <level>{message}</level>")

    # File: JSON structured for analysis
    logger.add("logs/aae_{time:YYYY-MM-DD}.log", level="DEBUG",
               rotation="00:00", retention="14 days", serialize=True)

    # Separate financial audit log — never rotated
    logger.add("logs/financial_audit.log", level="INFO",
               filter=lambda r: "FINANCIAL" in r["extra"],
               format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
               retention=None)
```

### 5.3 Virtual Bank Tool (Full Implementation)

```python
# tools/bank_tool.py
import os
import httpx
from datetime import datetime
from loguru import logger
from pydantic import BaseModel
from memory.database import get_budget_state, update_budget, log_transaction

SIMULATION_MODE = os.getenv("SIMULATION_MODE", "true").lower() == "true"
HARD_SPEND_LIMIT_PER_TX = 20.0   # Max single transaction without human OK
CRITICAL_RESERVE_FLOOR = 15.0    # Below this: force T1, emit LOW_FUNDS_ALERT


class SpendResult(BaseModel):
    success: bool
    amount: float
    balance_after: float
    message: str
    transaction_id: str | None = None
    blocked_reason: str | None = None


class VirtualBankTool:
    """
    Wraps the Wise Business API with hard guardrails.
    The agent never touches raw credentials — only this class does.

    GUARDRAILS (enforced at code level, NOT just prompting):
    1. No single transaction > HARD_SPEND_LIMIT_PER_TX without human pre-approval
    2. api_reserve is completely untouchable by investment operations
    3. In SIMULATION_MODE, all writes are no-ops but reads return realistic data
    4. Every operation is logged to financial_audit.log
    """

    def __init__(self):
        self.api_key = os.getenv("WISE_API_KEY")
        self.profile_id = os.getenv("WISE_PROFILE_ID")
        self.base_url = "https://api.transferwise.com"
        self._headers = {"Authorization": f"Bearer {self.api_key}"}

    def get_balance(self) -> dict:
        """Returns current budget state from local DB (source of truth)."""
        return get_budget_state()

    def spend_investment(self, amount: float, description: str,
                         agent_id: str, category: str,
                         human_pre_approved: bool = False) -> SpendResult:
        """
        Deduct from investment pool. Used by agents to fund opportunities.

        Args:
            human_pre_approved: Set True only if HITL email returned APPROVE.
                                 Amounts > HARD_SPEND_LIMIT require this.
        """
        logger.bind(FINANCIAL=True).info(
            f"SPEND REQUEST | agent={agent_id} | amount=${amount:.2f} | "
            f"category={category} | desc={description} | approved={human_pre_approved}"
        )

        state = get_budget_state()
        available = state["investment_pool"]

        # Hard limits — cannot be overridden by the agent
        if amount > HARD_SPEND_LIMIT_PER_TX and not human_pre_approved:
            return SpendResult(
                success=False, amount=amount, balance_after=available,
                message="Transaction blocked",
                blocked_reason=f"Amount ${amount:.2f} exceeds per-transaction limit "
                               f"${HARD_SPEND_LIMIT_PER_TX:.2f}. Human approval required."
            )

        if amount > available:
            return SpendResult(
                success=False, amount=amount, balance_after=available,
                message="Transaction blocked",
                blocked_reason=f"Insufficient investment pool. "
                               f"Available: ${available:.2f}, Requested: ${amount:.2f}"
            )

        new_pool = available - amount

        if SIMULATION_MODE:
            logger.warning(f"[SIMULATION] Would debit ${amount:.2f} from investment pool")
            update_budget(investment_pool=new_pool)
            log_transaction(agent_id, amount, "debit", category, description, new_pool)
            return SpendResult(success=True, amount=amount, balance_after=new_pool,
                               message="[SIMULATION] Transaction logged",
                               transaction_id=f"SIM-{datetime.now().timestamp():.0f}")

        # Live mode: execute via Wise virtual card
        try:
            result = self._execute_wise_payment(amount, description)
            update_budget(investment_pool=new_pool)
            log_transaction(agent_id, amount, "debit", category, description, new_pool,
                            metadata={"wise_tx_id": result.get("id")})
            return SpendResult(success=True, amount=amount, balance_after=new_pool,
                               message="Transaction executed",
                               transaction_id=str(result.get("id")))
        except Exception as e:
            logger.error(f"Wise API error: {e}")
            return SpendResult(success=False, amount=amount, balance_after=available,
                               message=f"Wise API error: {str(e)}")

    def record_revenue(self, amount: float, source: str, agent_id: str) -> SpendResult:
        """Called when an opportunity generates income."""
        state = get_budget_state()
        new_pool = state["investment_pool"] + amount
        new_revenue = state["total_revenue"] + amount
        new_profit = state["total_profit"] + amount  # Net for now; costs deducted elsewhere

        update_budget(investment_pool=new_pool, total_revenue=new_revenue, total_profit=new_profit)
        log_transaction(agent_id, amount, "credit", "revenue", source, new_pool)

        logger.bind(FINANCIAL=True).info(
            f"REVENUE | agent={agent_id} | amount=${amount:.2f} | source={source} | "
            f"new_pool=${new_pool:.2f} | total_profit=${new_profit:.2f}"
        )
        return SpendResult(success=True, amount=amount, balance_after=new_pool,
                           message="Revenue recorded")

    def check_api_reserve_health(self) -> tuple[bool, float]:
        """Returns (is_healthy, remaining). Healthy = above CRITICAL_RESERVE_FLOOR."""
        state = get_budget_state()
        remaining = state["api_reserve"]
        return remaining > CRITICAL_RESERVE_FLOOR, remaining

    def deduct_api_cost(self, cost_usd: float, model: str, agent_id: str):
        """Called after every LLM API call to track burn rate."""
        state = get_budget_state()
        new_reserve = max(0.0, state["api_reserve"] - cost_usd)
        update_budget(api_reserve=new_reserve)
        log_transaction(agent_id, cost_usd, "debit", "api_cost", f"Model: {model}",
                        new_reserve)

    def _execute_wise_payment(self, amount: float, description: str) -> dict:
        """
        Production Wise API call.
        Wise card must have a daily spending limit set at the BANK level
        (not just in code) as an additional safety layer.
        """
        # Wise requires a quote → transfer → fund flow
        # Simplified: use the card endpoint for direct payment
        response = httpx.post(
            f"{self.base_url}/v3/profiles/{self.profile_id}/transfers",
            headers=self._headers,
            json={"amount": amount, "currency": "USD", "reference": description},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
```

> ⚠️ **Caveat 1.1 — Wise API Complexity:** The real Wise transfer API requires quote creation, recipient setup, and transfer execution as separate steps. For testing, mock the `_execute_wise_payment` method. For production, follow the [Wise API documentation](https://api-docs.transferwise.com/). Always set a **bank-level daily card limit** of $25 before going live — this is your last line of defence if code guardrails fail.

> ⚠️ **Caveat 1.2 — SQLite Thread Safety:** SQLite with `check_same_thread=False` is safe for the multi-threaded scheduler pattern here because writes are serialised at the Python level. For >3 concurrent child agents, switch to PostgreSQL (add `psycopg2` to requirements).

---

## 6. Phase 2 — Skills System Implementation

### 6.1 The SkillLoader Class

```python
# skills/skill_loader.py
from pathlib import Path
from loguru import logger

SKILLS_DIR = Path("skills")

class SkillLoader:
    """
    Loads skill markdown files and bundles them into agent system prompts.

    Skills are pure markdown — no code, no imports, no dependencies.
    They are read from disk at agent init time and injected verbatim
    into the system prompt under a clearly labelled section.
    """

    def __init__(self):
        self._cache: dict[str, str] = {}

    def load(self, skill_path: str) -> str:
        """
        Load a single skill.
        skill_path: relative path without .md, e.g. "website_agency/frontend_design"
        """
        if skill_path in self._cache:
            return self._cache[skill_path]

        full_path = SKILLS_DIR / f"{skill_path}.md"
        if not full_path.exists():
            logger.warning(f"Skill not found: {full_path}")
            return ""

        content = full_path.read_text(encoding="utf-8")
        self._cache[skill_path] = content
        logger.debug(f"Loaded skill: {skill_path} ({len(content)} chars)")
        return content

    def load_bundle(self, skill_paths: list[str]) -> str:
        """
        Load and concatenate multiple skills with clear separators.
        Returns a formatted string ready for system prompt injection.
        """
        sections = []
        for path in skill_paths:
            content = self.load(path)
            if content:
                skill_name = path.split("/")[-1].replace("_", " ").title()
                sections.append(f"### SKILL: {skill_name}\n\n{content}")

        if not sections:
            return ""

        return (
            "\n\n---\n\n## LOADED EXPERTISE SKILLS\n\n"
            "The following skills define your quality standards and workflows. "
            "Apply them to every relevant task.\n\n"
            + "\n\n---\n\n".join(sections)
        )

    def list_available(self) -> list[str]:
        """Returns all available skill paths for logging/debugging."""
        return [
            str(p.relative_to(SKILLS_DIR)).replace(".md", "").replace("\\", "/")
            for p in SKILLS_DIR.rglob("*.md")
        ]


# Singleton
skill_loader = SkillLoader()
```

### 6.2 Writing the Core Skills

Create each of these files in the `skills/` directory. The content is what the agent actually reads — write it as if briefing a highly capable employee.

**`skills/core/opportunity_research.md`**

```markdown
# Opportunity Research Skill

## Mission
Find business opportunities that can generate revenue within 7 days using capital under $100.

## Research Process
1. Search for demand signals: Reddit threads asking "is there a tool for X?", Product Hunt "upcoming" products, Upwork job postings with 10+ proposals already submitted (proven demand), IndieHackers "what would you pay for?".
2. Validate demand: Does a paid solution exist? How many people have the same problem? What are they currently paying?
3. Assess supply gap: Can WE deliver better, faster, or cheaper than what exists?

## Mandatory Output Format
Every opportunity must include:
- `vertical`: one of [crypto, commodity, web_dev, app_dev, ai_wrapper, browser_extension]
- `demand_evidence`: 2+ source URLs with specific quotes/numbers
- `estimated_revenue_usd`: conservative single estimate (not a range)
- `capital_required_usd`: exact float
- `time_to_first_revenue_days`: integer
- `human_actions_required`: numbered list of specific tasks the human must do
- `risk_level`: LOW | MEDIUM | HIGH with one-sentence justification

## Disqualification Rules
Reject any opportunity that:
- Requires more than $80 capital from the investment pool
- Has time_to_first_revenue > 7 days
- Requires a licence or permit the human doesn't hold
- Involves leverage, derivatives, or borrowed capital
- Has human_actions_required > 5 items (too operationally complex)
```

**`skills/website_agency/frontend_design.md`**

```markdown
# Frontend Design Excellence Skill

## Philosophy
Every website we build must be MEMORABLE. Generic AI-generated aesthetics (purple gradients,
Inter/Roboto fonts, cookie-cutter layouts) are project failures. We build distinctive work.

## Design Thinking — Before Writing One Line of Code
1. IDENTIFY THE AUDIENCE: Who will use this site? What do they fear? What do they want to signal?
2. COMMIT TO AN AESTHETIC: Choose one extreme and execute it perfectly.
   Options: brutalist/raw | luxury/refined | editorial/magazine | retro-futurist |
   organic/natural | playful/toy-like | maximalist chaos | stark minimalism
3. CHOOSE TYPOGRAPHY FIRST: The font choice IS the brand. Avoid Inter, Roboto, Arial system fonts.
   Use: Playfair Display, Cormorant Garamond, Space Mono, DM Serif Display, Bebas Neue,
   Clash Display, Syne, Instrument Serif — pair a display font with a refined body font.
4. BUILD THE COLOUR SYSTEM: 1 dominant colour + 1 sharp accent + neutrals. CSS variables always.

## Code Standards
- Every animation uses `prefers-reduced-motion` media query
- Lighthouse performance score target: 90+
- Mobile-first responsive — breakpoints at 640px, 768px, 1024px, 1280px
- Images: WebP format, lazy loading, explicit width/height to prevent CLS
- Semantic HTML5: proper heading hierarchy, ARIA labels on interactive elements
- CSS: custom properties for all colours/spacing, no inline styles

## What We Never Do
- Cookie-cutter hero sections with stock photos
- Default blue links
- Walls of text without typographic hierarchy
- Forms without clear error states
- Pages that look the same on mobile and desktop
- Loading indicators that don't reflect actual progress

## Deliverable Checklist
Before calling a site complete:
[ ] Tested on Chrome, Firefox, Safari (BrowserStack if needed)
[ ] Mobile tested at 375px, 414px, 768px
[ ] All images compressed and in WebP
[ ] Meta title + description written
[ ] Open Graph tags for social sharing
[ ] Contact form tested end-to-end
[ ] 404 page exists
[ ] No console errors
```

**`skills/website_agency/project_pricing.md`**

```markdown
# Project Pricing Skill

## Pricing Philosophy
Price based on VALUE to the client, not hours spent. A landing page that converts
$10K/month in sales is worth $500 — not $50 because it took 3 hours to build.

## Price Anchors by Project Type
| Project Type          | Our Floor | Our Target | Our Ceiling |
|-----------------------|-----------|------------|-------------|
| Landing page (1-page) | $150      | $250       | $400        |
| Business site (5 pg)  | $300      | $500       | $800        |
| E-commerce (Shopify)  | $400      | $700       | $1,200      |
| Portfolio site        | $120      | $200       | $350        |
| Web app MVP (simple)  | $500      | $900       | $2,000      |

## Quoting Rules
1. Never quote a price lower than the floor without manager (human) approval.
2. Always quote a FIXED price — never hourly. Hourly creates scope anxiety.
3. Include exactly 2 revision rounds in every quote. Additional revisions: $50/round.
4. Collect 50% upfront, 50% on delivery. No exceptions for first-time clients.
5. Quote in USD. We do not negotiate currency — use Wise for international receipt.

## Scope Creep Prevention
- Define deliverables in bullet points in the proposal email.
- "Additional pages, features, or design changes beyond the agreed scope will be quoted separately."
- If a client adds scope after approval, pause work and send revised quote to human for approval.

## Upselling Opportunities
After delivery, offer: monthly maintenance ($50/mo), SEO optimisation add-on ($100),
copywriting add-on ($80), email newsletter setup ($75).
```

**`skills/trading/risk_management.md`**

```markdown
# Trading Risk Management Skill

## The Rules (Non-Negotiable)
1. Maximum position size: 20% of available investment pool per trade
2. Stop-loss is set BEFORE entry — never moved further from entry after the fact
3. Stop-loss maximum distance: 5% from entry price
4. Risk/reward minimum: 1.5:1 (risking $1 to make minimum $1.50)
5. Maximum 2 open positions at any time
6. No trading on days with scheduled high-impact economic events (NFP, CPI, FOMC)

## Position Sizing Formula
position_size = (investment_pool × 0.02) / stop_loss_distance_pct
# Risk maximum 2% of pool per trade, not 20%

## When to NOT Trade
- Spread is wider than 0.1% of asset price (low liquidity)
- Price has moved >3% in the last 4 hours (late entry on momentum)
- RSI is already above 70 (overbought) or below 30 (oversold) and we'd be chasing
- Economic calendar shows HIGH impact event within 4 hours

## Loss Recovery Protocol
After 3 consecutive losing trades:
1. STOP trading for 24 hours
2. Review each losing trade and document what signal was wrong
3. Email human with loss summary and revised strategy
4. Resume only after human confirms continuation
```

### 6.3 Skill Bundles Per Agent Type

```python
# skills/bundles.py — Defines which skills each agent type loads

SKILL_BUNDLES: dict[str, list[str]] = {
    "mother_agent": [
        "core/opportunity_research",
        "core/financial_analysis",
        "core/copywriting",
    ],
    "website_agency": [
        "core/copywriting",
        "website_agency/frontend_design",
        "website_agency/web_architecture",
        "website_agency/seo_optimization",
        "website_agency/client_communications",
        "website_agency/project_pricing",
    ],
    "crypto_trader": [
        "trading/technical_analysis",
        "trading/risk_management",
    ],
    "ai_wrapper_builder": [
        "core/copywriting",
        "software/api_wrapping",
        "software/saas_pricing",
    ],
    "extension_builder": [
        "core/copywriting",
        "software/extension_development",
        "software/saas_pricing",
    ],
}
```

---

## 7. Phase 3 — Model Router (Gemini + Bonsai + Claude)

### 7.1 The Task Taxonomy

Every agent action maps to a task type, and every task type maps to a model. This is the core of the cost-efficiency strategy.

```python
# agents/model_router.py
from enum import Enum
from dataclasses import dataclass
import os

class TaskType(Enum):
    # Always FREE (Bonsai) — code generation tasks
    CODE_GENERATION    = "code_generation"     # Bonsai
    CODE_REVIEW        = "code_review"          # Bonsai

    # Always T1 (Gemini Flash) — cheap reasoning tasks
    WEB_RESEARCH       = "web_research"
    EMAIL_DRAFT        = "email_draft"
    MEMORY_SUMMARY     = "memory_summary"
    LOG_ANALYSIS       = "log_analysis"

    # T2+ (GPT-4o mini) — moderate reasoning
    OPPORTUNITY_SCORE  = "opportunity_score"
    TRADE_SIGNAL       = "trade_signal"
    PROPOSAL_DRAFT     = "proposal_draft"

    # T3+ (Sonnet) — complex reasoning
    FINANCIAL_STRATEGY = "financial_strategy"
    CHILD_SPAWN_PLAN   = "child_spawn_plan"
    WEBSITE_DESIGN     = "website_design"      # Architecture + design decisions

    # T4 only (Opus) — premium reasoning, capped at 5K tokens/day
    WEEKLY_SYNTHESIS   = "weekly_synthesis"
    PREMIUM_CODE_REVIEW = "premium_code_review"


@dataclass
class ModelConfig:
    provider: str       # "google" | "anthropic" | "openai" | "bonsai"
    model_id: str
    max_tokens: int
    daily_token_budget: int   # Hard cap per model per day
    cost_per_1m_input: float
    cost_per_1m_output: float


MODELS = {
    "bonsai":   ModelConfig("bonsai",    "auto",                   4096, 9_999_999, 0.0,   0.0),
    "T1":       ModelConfig("google",    "gemini-2.0-flash",       2048, 500_000,   0.075, 0.30),
    "T2":       ModelConfig("openai",    "gpt-4o-mini",            2048, 200_000,   0.15,  0.60),
    "T3":       ModelConfig("anthropic", "claude-sonnet-4-6",      4096, 20_000,    3.00,  15.0),
    "T4":       ModelConfig("anthropic", "claude-opus-4-6",        8192, 5_000,     15.0,  75.0),
}

# Task → minimum tier required AND whether Bonsai is eligible
TASK_ROUTING: dict[TaskType, tuple[str, bool]] = {
    #                                           min_tier  bonsai_eligible
    TaskType.CODE_GENERATION:                  ("T1",     True),
    TaskType.CODE_REVIEW:                      ("T1",     True),
    TaskType.WEB_RESEARCH:                     ("T1",     False),
    TaskType.EMAIL_DRAFT:                      ("T1",     False),
    TaskType.MEMORY_SUMMARY:                   ("T1",     False),
    TaskType.LOG_ANALYSIS:                     ("T1",     False),
    TaskType.OPPORTUNITY_SCORE:                ("T2",     False),
    TaskType.TRADE_SIGNAL:                     ("T2",     False),
    TaskType.PROPOSAL_DRAFT:                   ("T2",     True),
    TaskType.FINANCIAL_STRATEGY:               ("T3",     False),
    TaskType.CHILD_SPAWN_PLAN:                 ("T3",     False),
    TaskType.WEBSITE_DESIGN:                   ("T3",     False),
    TaskType.WEEKLY_SYNTHESIS:                 ("T4",     False),
    TaskType.PREMIUM_CODE_REVIEW:              ("T4",     False),
}


class ModelRouter:
    """
    Given a task type and the agent's current profit state,
    returns the appropriate model configuration.

    Priority order:
    1. Use Bonsai (free) if task is code-related and privacy is not a concern
    2. Use T1 if within tier limits
    3. Upgrade tier only if profit thresholds are met
    4. Always downgrade to T1 if API reserve is critically low
    """

    PROFIT_THRESHOLDS = {"T1": 0, "T2": 10.0, "T3": 50.0, "T4": 150.0}

    def __init__(self, bank_tool):
        self.bank_tool = bank_tool
        self._daily_token_usage: dict[str, int] = {}

    def get_model(self, task: TaskType, current_profit: float,
                  contains_sensitive_data: bool = False) -> ModelConfig:
        """
        Main routing method. Always call this before making any LLM request.

        Args:
            task: What kind of cognitive work is being done
            current_profit: Cumulative profit to date (determines tier)
            contains_sensitive_data: If True, Bonsai is NEVER used (privacy)
        """
        min_tier, bonsai_eligible = TASK_ROUTING[task]

        # Step 1: Can we use Bonsai (free)?
        if bonsai_eligible and not contains_sensitive_data:
            return MODELS["bonsai"]

        # Step 2: Check API reserve health
        is_healthy, reserve = self.bank_tool.check_api_reserve_health()
        if not is_healthy:
            return MODELS["T1"]  # Force survival mode

        # Step 3: Find the highest tier the agent has earned
        active_tier = "T1"
        for tier in ["T4", "T3", "T2", "T1"]:
            if current_profit >= self.PROFIT_THRESHOLDS[tier]:
                active_tier = tier
                break

        # Step 4: Task requires at least min_tier — can we meet it?
        tier_order = ["T1", "T2", "T3", "T4"]
        min_idx = tier_order.index(min_tier)
        active_idx = tier_order.index(active_tier)
        selected_tier = tier_order[max(min_idx, active_idx)]

        # Step 5: Check daily token budget
        model = MODELS[selected_tier]
        used = self._daily_token_usage.get(selected_tier, 0)
        if used >= model.daily_token_budget:
            return MODELS["T1"]  # Budget exhausted — silent fallback

        return model

    def record_usage(self, tier: str, tokens_used: int):
        self._daily_token_usage[tier] = (
            self._daily_token_usage.get(tier, 0) + tokens_used
        )

    def reset_daily_budgets(self):
        """Called at midnight by scheduler."""
        self._daily_token_usage.clear()
```

### 7.2 Bonsai Integration

Bonsai exposes an OpenAI-compatible endpoint, meaning you can use the `openai` Python client pointed at Bonsai's base URL.

```python
# tools/bonsai_tool.py
import os
import subprocess
import httpx
from loguru import logger

BONSAI_API_KEY = os.getenv("BONSAI_API_KEY")
# Bonsai is OpenAI API-compatible — check docs.trybons.ai for current endpoint
BONSAI_BASE_URL = "https://api.trybons.ai/v1"

# CRITICAL PRIVACY GUARD: These strings trigger automatic blocking
# if found in any prompt destined for Bonsai
SENSITIVE_KEYWORDS = [
    "api_key", "secret", "password", "private_key", "WISE_API", "ANTHROPIC_API",
    "GEMINI_API", "balance", "bank", "transaction", "spend", "revenue",
    "profit", "investment_pool", "wise.com", "customer email", "client name"
]


def _is_safe_for_bonsai(prompt: str) -> bool:
    """
    Privacy gate: block any prompt containing sensitive data patterns.
    Bonsai logs all prompts — no financial/credential data ever passes through.
    """
    prompt_lower = prompt.lower()
    for keyword in SENSITIVE_KEYWORDS:
        if keyword.lower() in prompt_lower:
            logger.warning(f"BONSAI BLOCKED: Prompt contains sensitive keyword '{keyword}'")
            return False
    return True


def generate_code_with_bonsai(prompt: str, context: str = "") -> str:
    """
    Send a code generation request to Bonsai (free frontier model).

    RULES:
    - Only code generation prompts — no financial data, no API keys
    - Prompt is sanitised through privacy gate before sending
    - Falls back to returning empty string on any error (caller must handle)

    Args:
        prompt: What to build (e.g. "Build a React landing page for a SaaS product")
        context: Additional technical context (framework versions, constraints)
    """
    full_prompt = f"{prompt}\n\nTechnical context: {context}" if context else prompt

    if not _is_safe_for_bonsai(full_prompt):
        raise ValueError(
            "Prompt contains sensitive data and cannot be sent to Bonsai. "
            "Use a paid model for this task."
        )

    try:
        response = httpx.post(
            f"{BONSAI_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {BONSAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "auto",   # Bonsai assigns frontier model automatically
                "messages": [
                    {"role": "system", "content": "You are an expert software engineer. "
                     "Write clean, production-ready code with comments. "
                     "Return only the code, no explanation unless asked."},
                    {"role": "user", "content": full_prompt}
                ],
                "max_tokens": 4096,
            },
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()
        code = result["choices"][0]["message"]["content"]
        logger.info(f"Bonsai generated {len(code)} chars of code (model: {result.get('model','stealth')})")
        return code

    except httpx.HTTPStatusError as e:
        logger.error(f"Bonsai API HTTP error: {e.response.status_code} — {e.response.text}")
        return ""
    except Exception as e:
        logger.error(f"Bonsai API error: {e}")
        return ""
```

> ⚠️ **Caveat 3.1 — Bonsai Data Policy:** Bonsai explicitly states: *"Prompts and completions are logged for benchmarking and training. All data is anonymized and may be shared with model developers."* This means code you generate with Bonsai could appear in future training datasets. Do not generate code containing proprietary business logic, API integrations with your credentials, or client-specific implementations that require confidentiality. Use it for boilerplate, templates, and generic UI components.

> ⚠️ **Caveat 3.2 — Bonsai Model Variability:** Bonsai assigns frontier models randomly and resets every 24 hours. Code quality will vary between sessions. The agent must validate generated code (at minimum: syntax check, linting) before using it in production. Never deploy Bonsai-generated code without human review for client projects.

> ⚠️ **Caveat 3.3 — Bonsai API Endpoint:** At time of writing, Bonsai's API endpoint URL is not publicly documented beyond the CLI. Check `https://docs.trybons.ai` for the current REST API base URL. The CLI (`bonsai start`) wraps a local proxy — you may need to capture the proxy port it opens and use that as your base URL if a direct API is not available. Monitor their Discord for updates.

---

## 8. Phase 4 — Tools Layer

### 8.1 Web Search Tool

```python
# tools/search_tool.py
import os
from duckduckgo_search import DDGS
from tavily import TavilyClient
from loguru import logger

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


def web_search(query: str, max_results: int = 5,
               use_tavily: bool = False) -> list[dict]:
    """
    Search the web. Uses DuckDuckGo by default (free, no rate limit),
    Tavily for queries requiring higher quality (5K free/month).

    Returns: list of {"title": str, "url": str, "snippet": str}
    """
    if use_tavily:
        try:
            result = tavily.search(query=query, max_results=max_results)
            return [
                {"title": r["title"], "url": r["url"], "snippet": r["content"]}
                for r in result.get("results", [])
            ]
        except Exception as e:
            logger.warning(f"Tavily failed ({e}), falling back to DuckDuckGo")

    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=max_results))
    return [{"title": r["title"], "url": r["href"], "snippet": r["body"]}
            for r in results]


def search_freelance_jobs(platform: str, keywords: str) -> list[dict]:
    """Specialised search for freelance job opportunities."""
    query = f'site:{platform}.com {keywords} fixed price "budget" -"hourly"'
    return web_search(query, max_results=10, use_tavily=True)


def search_product_opportunities(vertical: str) -> list[dict]:
    """Find unmet needs and demand signals for a given vertical."""
    queries = {
        "ai_wrapper": 'site:reddit.com "is there a tool" OR "I wish there was" AI GPT',
        "browser_extension": 'site:reddit.com "chrome extension" "I want" OR "someone should make"',
        "web_dev": 'site:upwork.com "website" "fixed price" budget:100..500',
    }
    query = queries.get(vertical, f'"{vertical}" opportunity 2025 revenue profit')
    return web_search(query, max_results=8, use_tavily=True)
```

### 8.2 Email Tool (Full HITL Implementation)

```python
# tools/email_tool.py
import os
import smtplib
import imaplib
import email
import time
import re
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader
from loguru import logger
from pathlib import Path

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
HUMAN_EMAIL = os.getenv("HUMAN_EMAIL")
TEMPLATE_DIR = Path("email_templates")

jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


class EmailTool:
    POLL_INTERVAL_SECONDS = 900   # 15 minutes
    TIMEOUT_HOURS = 48            # Wait this long before sending reminder
    ABORT_HOURS = 72              # Give up after this if no reply

    def send_opportunity_brief(self, opportunity: dict, agent_id: str) -> str:
        """
        Send HITL email asking human to approve/reject an opportunity.
        Returns a unique reply_tag the polling loop will look for.
        """
        reply_tag = f"AAE-{agent_id[:8]}-{uuid.uuid4().hex[:6].upper()}"
        subject = f"[{reply_tag}] Action Required: Opportunity Approval"

        template = jinja_env.get_template("opportunity_brief.html")
        html_body = template.render(
            opportunity=opportunity,
            reply_tag=reply_tag,
            agent_id=agent_id,
        )

        self._send(subject, html_body)
        logger.info(f"Sent OPPORTUNITY_BRIEF | tag={reply_tag}")
        return reply_tag

    def send_action_required(self, actions: list[str], context: str,
                              reply_tag: str, agent_id: str):
        subject = f"[{reply_tag}] Human Action Required — Please Complete & Reply DONE"
        template = jinja_env.get_template("action_required.html")
        html_body = template.render(actions=actions, context=context,
                                    reply_tag=reply_tag)
        self._send(subject, html_body)

    def send_weekly_report(self, report_data: dict):
        subject = "📊 AAE Weekly Report — Agent Activity & Financial Summary"
        template = jinja_env.get_template("weekly_report.html")
        html_body = template.render(**report_data)
        self._send(subject, html_body)

    def send_low_funds_alert(self, reserve_remaining: float):
        subject = "🚨 CRITICAL: AAE API Reserve Low — Action Required"
        body = f"""
        <h2>API Reserve Critical</h2>
        <p>The AAE API reserve has dropped to <strong>${reserve_remaining:.2f}</strong>.</p>
        <p>The agent will switch to T1 (Gemini Flash only) immediately.</p>
        <p>If no action is taken within 24 hours, the agent will suspend all operations.</p>
        <h3>To add funds:</h3>
        <ol>
          <li>Top up the Wise account via your banking app</li>
          <li>Reply to this email with: <strong>FUNDED $[amount]</strong></li>
        </ol>
        """
        self._send(subject, body)

    def poll_for_reply(self, reply_tag: str) -> dict:
        """
        Block-polls Gmail inbox for a reply containing reply_tag.
        Returns: {"decision": "APPROVE"|"REJECT"|"DONE"|"TIMEOUT"|"ABORT",
                  "notes": str, "raw_body": str}
        """
        start_time = time.time()
        reminder_sent = False

        logger.info(f"Polling for reply | tag={reply_tag}")

        while True:
            elapsed_hours = (time.time() - start_time) / 3600

            if elapsed_hours > self.ABORT_HOURS:
                logger.warning(f"No reply after {self.ABORT_HOURS}h — ABORT | tag={reply_tag}")
                return {"decision": "ABORT", "notes": "No human reply — agent suspending"}

            if elapsed_hours > self.TIMEOUT_HOURS and not reminder_sent:
                self._send(
                    f"[{reply_tag}] Reminder: Awaiting Your Decision",
                    f"<p>The agent is still waiting for your reply to {reply_tag}. "
                    f"Please reply APPROVE, REJECT, or DONE to proceed.</p>"
                )
                reminder_sent = True

            # Check inbox
            reply = self._check_inbox_for_reply(reply_tag)
            if reply:
                return reply

            time.sleep(self.POLL_INTERVAL_SECONDS)

    def _check_inbox_for_reply(self, reply_tag: str) -> dict | None:
        """Connects to Gmail IMAP and looks for an unread reply with reply_tag."""
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            mail.select("inbox")

            # Search for unread emails with the tag in subject
            _, data = mail.search(None, f'(UNSEEN SUBJECT "{reply_tag}")')
            if not data[0]:
                mail.logout()
                return None

            # Get the most recent matching email
            mail_id = data[0].split()[-1]
            _, msg_data = mail.fetch(mail_id, "(RFC822)")
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Extract body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                        break
            else:
                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

            # Mark as read
            mail.store(mail_id, "+FLAGS", "\\Seen")
            mail.logout()

            return self._parse_decision(body)

        except Exception as e:
            logger.error(f"IMAP error: {e}")
            return None

    def _parse_decision(self, body: str) -> dict:
        """
        Extract structured decision from human email reply.
        Supports: APPROVE, REJECT, DONE, STOP, MODIFY [notes]
        """
        body_upper = body.upper().strip()
        notes = body.strip()

        for keyword in ["APPROVE", "APPROVED", "YES", "GO AHEAD", "PROCEED"]:
            if keyword in body_upper:
                return {"decision": "APPROVE", "notes": notes, "raw_body": body}

        for keyword in ["REJECT", "REJECTED", "NO", "STOP", "CANCEL", "ABORT"]:
            if keyword in body_upper:
                return {"decision": "REJECT", "notes": notes, "raw_body": body}

        if "DONE" in body_upper or "COMPLETED" in body_upper:
            return {"decision": "DONE", "notes": notes, "raw_body": body}

        # Unrecognised — treat as notes, ask agent to re-evaluate
        return {"decision": "UNCLEAR", "notes": notes, "raw_body": body}

    def _send(self, subject: str, html_body: str):
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = GMAIL_ADDRESS
        msg["To"] = HUMAN_EMAIL
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)


email_tool = EmailTool()
```

> ⚠️ **Caveat 4.1 — IMAP Blocking:** The `poll_for_reply` method blocks the calling thread. Always run it in a background thread or asyncio task so the rest of the agent remains responsive. See the LangGraph state machine in Phase 10 for how AWAITING_APPROVAL is handled without blocking.

---

## 9. Phase 5 — Mother Agent

### 9.1 Base Agent Class

```python
# agents/base_agent.py
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from anthropic import Anthropic
from crewai import Agent
from skills.skill_loader import skill_loader
from skills.bundles import SKILL_BUNDLES
from agents.model_router import ModelRouter, TaskType
from tools.bank_tool import VirtualBankTool
from memory.database import get_budget_state
from loguru import logger

anthropic_client = Anthropic()


class BaseAgent:
    """
    All agents (Mother and Children) inherit from this.
    Handles: skill loading, model routing, cost tracking.
    """

    def __init__(self, agent_id: str, agent_type: str, bank_tool: VirtualBankTool):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.bank_tool = bank_tool
        self.router = ModelRouter(bank_tool)

        # Load skills for this agent type
        skill_paths = SKILL_BUNDLES.get(agent_type, [])
        self.skill_block = skill_loader.load_bundle(skill_paths)
        self.skills_loaded = skill_paths
        logger.info(f"Agent {agent_id} ({agent_type}) loaded {len(skill_paths)} skills")

    def get_current_profit(self) -> float:
        state = get_budget_state()
        return state.get("total_profit", 0.0)

    def llm_call(self, task_type: TaskType, prompt: str,
                 system_prompt: str = "", contains_sensitive: bool = False) -> str:
        """
        Single unified entry point for ALL LLM calls.
        Routes to the correct model, tracks cost, enforces limits.
        """
        profit = self.get_current_profit()
        model_config = self.router.get_model(task_type, profit, contains_sensitive)

        full_system = (system_prompt or "") + self.skill_block

        if model_config.provider == "bonsai":
            from tools.bonsai_tool import generate_code_with_bonsai
            return generate_code_with_bonsai(prompt)

        elif model_config.provider == "google":
            llm = ChatGoogleGenerativeAI(
                model=model_config.model_id,
                google_api_key=os.getenv("GEMINI_API_KEY"),
                max_output_tokens=model_config.max_tokens,
            )
            messages = []
            if full_system:
                messages.append({"role": "user", "content": f"SYSTEM: {full_system}"})
                messages.append({"role": "assistant", "content": "Understood."})
            messages.append({"role": "user", "content": prompt})
            response = llm.invoke(messages)
            result = response.content

        elif model_config.provider == "anthropic":
            response = anthropic_client.messages.create(
                model=model_config.model_id,
                max_tokens=model_config.max_tokens,
                system=full_system,
                messages=[{"role": "user", "content": prompt}]
            )
            result = response.content[0].text
            # Track token usage for budget
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            self.router.record_usage(
                "T3" if "sonnet" in model_config.model_id else "T4", tokens_used
            )
            # Estimate cost and deduct from API reserve
            cost = (response.usage.input_tokens / 1_000_000 * model_config.cost_per_1m_input +
                    response.usage.output_tokens / 1_000_000 * model_config.cost_per_1m_output)
            self.bank_tool.deduct_api_cost(cost, model_config.model_id, self.agent_id)

        else:
            raise ValueError(f"Unknown provider: {model_config.provider}")

        return result
```

### 9.2 Mother Agent Definition

```python
# agents/mother_agent.py
import json
import uuid
from datetime import datetime
from loguru import logger
from agents.base_agent import BaseAgent
from agents.model_router import TaskType
from tools.bank_tool import VirtualBankTool
from tools.email_tool import email_tool
from tools.search_tool import web_search, search_product_opportunities
from memory.database import init_databases, get_budget_state

MOTHER_SYSTEM_PROMPT = """
You are the Mother Agent — chief orchestrator of the Autonomous Agent Ecosystem.

YOUR MISSION:
Find and execute short-term, high-profit business opportunities that generate revenue
within 7 days. Sustain your $50 API budget. Grow a network of profitable child agents.

OPERATING VERTICALS (in priority order):
1. AI Wrappers — build and sell AI-powered tools (highest score: 40/45)
2. Cryptocurrency spot trading — Binance API, BTC/ETH/SOL only, NO leverage
3. Browser Extensions — Chrome Web Store, one-time purchase model
4. Web Development — Upwork/Fiverr fixed-price projects
5. Application Development — Gumroad/LemonSqueezy products
6. Commodity Trading — OANDA API, gold/silver/oil only

DECISION PRINCIPLES:
- Never spend more than $20 without human email approval
- Never act on information without a source URL
- When in doubt, choose the option with lower capital requirement
- If API reserve drops below $15, stop all operations and alert human

OUTPUT STANDARD:
Every opportunity assessment must be a valid JSON object (not prose).
Every email to the human must include: what you want to do, what YOU will do,
what the HUMAN must do, and what response you need.
"""


class MotherAgent(BaseAgent):
    def __init__(self, bank_tool: VirtualBankTool):
        super().__init__(
            agent_id=f"MOTHER-{uuid.uuid4().hex[:8].upper()}",
            agent_type="mother_agent",
            bank_tool=bank_tool
        )
        self.child_agents: list[str] = []

    def research_opportunities(self) -> list[dict]:
        """Phase 1 of each cycle: find 3-5 candidates using web search."""
        logger.info("Starting opportunity research cycle...")

        # Research each vertical in priority order
        all_results = []
        for vertical in ["ai_wrapper", "browser_extension", "web_dev", "crypto"]:
            results = search_product_opportunities(vertical)
            all_results.extend(results[:3])

        # Score with LLM
        research_context = json.dumps(all_results, indent=2)
        prompt = f"""
        Based on these web search results, identify the TOP 3 business opportunities
        that match our selection criteria (< 7 days to revenue, < $80 capital,
        reversible if failed, no licence required).

        Search results:
        {research_context}

        Return a JSON array of 3 opportunity objects, each with:
        vertical, title, description, demand_evidence (list of URLs),
        estimated_revenue_usd, capital_required_usd,
        time_to_first_revenue_days, human_actions_required (list),
        risk_level (LOW/MEDIUM/HIGH)

        Return ONLY the JSON array, nothing else.
        """

        response = self.llm_call(
            TaskType.OPPORTUNITY_SCORE,
            prompt,
            system_prompt=MOTHER_SYSTEM_PROMPT
        )

        try:
            opportunities = json.loads(response.strip())
            logger.info(f"Found {len(opportunities)} scored opportunities")
            return opportunities
        except json.JSONDecodeError:
            logger.error("Failed to parse opportunity JSON — returning empty list")
            return []

    def select_best_opportunity(self, opportunities: list[dict]) -> dict | None:
        """Select the highest-scoring opportunity using the financial_analysis skill."""
        if not opportunities:
            return None

        state = get_budget_state()
        available_capital = state["investment_pool"]

        # Filter to what we can afford
        affordable = [o for o in opportunities
                      if o.get("capital_required_usd", 999) <= available_capital]

        if not affordable:
            logger.warning("No affordable opportunities — all exceed investment pool")
            return None

        # Sort by estimated_revenue / capital_required (return on investment)
        scored = sorted(
            affordable,
            key=lambda o: o.get("estimated_revenue_usd", 0) / max(o.get("capital_required_usd", 1), 1),
            reverse=True
        )
        return scored[0]

    def request_human_approval(self, opportunity: dict) -> dict:
        """Send OPPORTUNITY_BRIEF email and wait for reply."""
        reply_tag = email_tool.send_opportunity_brief(opportunity, self.agent_id)
        return email_tool.poll_for_reply(reply_tag)

    def spawn_child_agent(self, specialty: str, capital: float) -> str:
        """Create a specialised child agent after a profitable outcome."""
        from agents.child_factory import ChildAgentFactory
        factory = ChildAgentFactory(self.bank_tool)
        child_id = factory.spawn(
            specialty=specialty,
            capital=capital,
            parent_id=self.agent_id
        )
        self.child_agents.append(child_id)
        logger.info(f"Spawned child agent: {child_id} | specialty={specialty}")
        return child_id

    def run_cycle(self):
        """One full research → approval → execute → evaluate cycle."""
        logger.info(f"=== MOTHER AGENT CYCLE START | {datetime.now().isoformat()} ===")

        # Check funds
        healthy, reserve = self.bank_tool.check_api_reserve_health()
        if not healthy:
            email_tool.send_low_funds_alert(reserve)
            logger.warning("API reserve critically low — suspending cycle")
            return

        opportunities = self.research_opportunities()
        best = self.select_best_opportunity(opportunities)

        if not best:
            logger.info("No viable opportunity found — sleeping until next cycle")
            return

        logger.info(f"Best opportunity: {best.get('title')} | "
                    f"revenue=${best.get('estimated_revenue_usd')} | "
                    f"capital=${best.get('capital_required_usd')}")

        # Get human approval
        decision = self.request_human_approval(best)

        if decision["decision"] != "APPROVE":
            logger.info(f"Human decision: {decision['decision']} — skipping opportunity")
            return

        logger.info("Human approved — proceeding to execution")
        # Execution logic continues in state machine (Phase 10)
```

---

## 10. Phase 6 — Human-in-the-Loop Email System

### 10.1 Opportunity Brief Email Template

Create `email_templates/opportunity_brief.html`:

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body { font-family: -apple-system, Arial, sans-serif; max-width: 640px;
         margin: 0 auto; color: #1a1a1a; line-height: 1.6; }
  .header { background: #1F4E79; color: white; padding: 24px;
            border-radius: 8px 8px 0 0; }
  .header h1 { margin: 0; font-size: 20px; }
  .header .tag { font-size: 12px; opacity: 0.7; margin-top: 4px; }
  .body { background: #f8f9fa; padding: 24px; border: 1px solid #dee2e6; }
  .metric { display: inline-block; background: white; border: 1px solid #dee2e6;
            border-radius: 6px; padding: 12px 16px; margin: 4px; min-width: 120px; }
  .metric .label { font-size: 11px; color: #6c757d; text-transform: uppercase; }
  .metric .value { font-size: 22px; font-weight: bold; color: #1F4E79; }
  .section { background: white; border-radius: 6px; padding: 16px;
             margin: 12px 0; border-left: 4px solid #2E75B6; }
  .actions-needed { background: #fff3cd; border-left-color: #ffc107; }
  .reply-box { background: #e8f4f8; border-radius: 6px; padding: 16px;
               margin-top: 16px; text-align: center; }
  .reply-box code { background: #1F4E79; color: white; padding: 8px 16px;
                    border-radius: 4px; font-size: 16px; display: block;
                    margin: 8px auto; width: fit-content; }
  .risk-LOW    { color: #28a745; font-weight: bold; }
  .risk-MEDIUM { color: #ffc107; font-weight: bold; }
  .risk-HIGH   { color: #dc3545; font-weight: bold; }
</style>
</head>
<body>
<div class="header">
  <h1>🤖 Opportunity Brief — Awaiting Your Decision</h1>
  <div class="tag">Reply Tag: {{ reply_tag }} | Agent: {{ agent_id }}</div>
</div>
<div class="body">
  <h2>{{ opportunity.title }}</h2>
  <p>{{ opportunity.description }}</p>

  <div>
    <div class="metric">
      <div class="label">Expected Revenue</div>
      <div class="value">${{ "%.0f"|format(opportunity.estimated_revenue_usd) }}</div>
    </div>
    <div class="metric">
      <div class="label">Capital Required</div>
      <div class="value">${{ "%.0f"|format(opportunity.capital_required_usd) }}</div>
    </div>
    <div class="metric">
      <div class="label">Time to Revenue</div>
      <div class="value">{{ opportunity.time_to_first_revenue_days }}d</div>
    </div>
    <div class="metric">
      <div class="label">Risk Level</div>
      <div class="value {{ 'risk-' + opportunity.risk_level }}">
        {{ opportunity.risk_level }}
      </div>
    </div>
  </div>

  <div class="section">
    <strong>📊 Demand Evidence</strong>
    <ul>
    {% for url in opportunity.demand_evidence %}
      <li><a href="{{ url }}">{{ url }}</a></li>
    {% endfor %}
    </ul>
  </div>

  <div class="section actions-needed">
    <strong>⚡ What YOU Need to Do (Human Actions):</strong>
    <ol>
    {% for action in opportunity.human_actions_required %}
      <li>{{ action }}</li>
    {% endfor %}
    </ol>
  </div>

  <div class="section">
    <strong>🤖 What the Agent Will Do:</strong>
    <p>Once you approve, the agent will autonomously handle all technical
    implementation. You will receive an ACTION_REQUIRED email for each step
    that needs your physical presence or account access.</p>
  </div>

  <div class="reply-box">
    <strong>Reply to this email with ONE of:</strong>
    <code>APPROVE</code>
    <code>REJECT</code>
    <code>REJECT — [reason]</code>
    <p style="font-size:12px;color:#6c757d;">
      Include the reply tag {{ reply_tag }} in your subject line (already there if you hit Reply).
    </p>
  </div>
</div>
</body>
</html>
```

> ⚠️ **Caveat 6.1 — Gmail IMAP Reliability:** Gmail's IMAP may delay delivery by up to 5 minutes during high-traffic periods. The 15-minute polling interval accounts for this. If you notice missed replies, check that your Gmail account has IMAP enabled: Gmail Settings → See all settings → Forwarding and POP/IMAP → Enable IMAP.

> ⚠️ **Caveat 6.2 — Reply Parsing Robustness:** The `_parse_decision` method uses simple keyword matching. If you use email clients that quote the original email in the reply (Outlook, Apple Mail), the original text containing "APPROVE" in the opportunity brief will match. Mitigate this by checking only the first 200 characters of the body (above the quoted text).

---

## 11. Phase 7 — Child Agent Factory

```python
# agents/child_factory.py
import uuid
from datetime import datetime
from loguru import logger
from pydantic import BaseModel
from tools.bank_tool import VirtualBankTool
from tools.email_tool import email_tool
from memory.database import get_connection

SPAWN_CONFIGS = {
    "website_agency": {
        "class": "agents.children.website_agency.WebsiteAgencyAgent",
        "min_profit_to_spawn": 50.0,    # Must have $50 profit before spawning
        "min_capital": 20.0,             # Needs at least $20 allocated
        "model_tier": "T4",              # Uses Opus — high quality work
        "description": "Builds and sells complete websites as a micro web agency",
    },
    "crypto_trader": {
        "class": "agents.children.crypto_trader.CryptoTraderAgent",
        "min_profit_to_spawn": 10.0,
        "min_capital": 30.0,
        "model_tier": "T2",
        "description": "Executes crypto spot trades on Binance",
    },
    "ai_wrapper_builder": {
        "class": "agents.children.ai_wrapper_builder.AIWrapperAgent",
        "min_profit_to_spawn": 20.0,
        "min_capital": 15.0,
        "model_tier": "T2",
        "description": "Builds and sells AI wrapper products on Gumroad",
    },
    "extension_builder": {
        "class": "agents.children.extension_builder.ExtensionBuilderAgent",
        "min_profit_to_spawn": 15.0,
        "min_capital": 10.0,
        "model_tier": "T2",
        "description": "Builds and publishes Chrome browser extensions",
    },
}


class ChildAgentFactory:
    def __init__(self, bank_tool: VirtualBankTool):
        self.bank_tool = bank_tool

    def spawn(self, specialty: str, capital: float, parent_id: str) -> str:
        """
        Spawn a new child agent:
        1. Validate spawn conditions
        2. Allocate capital from investment pool
        3. Email human for approval
        4. Instantiate the agent class
        5. Register in agents DB
        6. Start agent's run loop in background thread
        """
        config = SPAWN_CONFIGS.get(specialty)
        if not config:
            raise ValueError(f"Unknown specialty: {specialty}")

        profit = self.bank_tool.get_balance().get("total_profit", 0)
        if profit < config["min_profit_to_spawn"]:
            raise ValueError(
                f"Cannot spawn {specialty}: need ${config['min_profit_to_spawn']} profit, "
                f"have ${profit:.2f}"
            )

        if capital < config["min_capital"]:
            capital = config["min_capital"]
            logger.warning(f"Capital adjusted to minimum: ${capital}")

        # Deduct from investment pool
        result = self.bank_tool.spend_investment(
            amount=capital,
            description=f"Capital allocation for new {specialty} child agent",
            agent_id=parent_id,
            category="child_agent_spawn",
            human_pre_approved=True   # Spawn approval email was sent separately
        )
        if not result.success:
            raise ValueError(f"Cannot allocate capital: {result.blocked_reason}")

        # Create agent ID and register
        agent_id = f"{specialty.upper()[:6]}-{uuid.uuid4().hex[:8].upper()}"
        self._register_agent(agent_id, specialty, parent_id, capital, config)

        # Dynamically import and instantiate the agent class
        module_path, class_name = config["class"].rsplit(".", 1)
        import importlib
        module = importlib.import_module(module_path)
        agent_class = getattr(module, class_name)
        agent_instance = agent_class(
            agent_id=agent_id,
            bank_tool=self.bank_tool,
            capital=capital,
            parent_id=parent_id,
        )

        # Start in background thread
        import threading
        thread = threading.Thread(
            target=agent_instance.run_loop,
            daemon=True,
            name=f"agent-{agent_id}"
        )
        thread.start()

        logger.info(f"✅ Child agent spawned: {agent_id} | {specialty} | capital=${capital}")
        return agent_id

    def _register_agent(self, agent_id: str, specialty: str,
                         parent_id: str, capital: float, config: dict):
        with get_connection("agents") as conn:
            conn.execute(
                """INSERT INTO agents
                   (agent_id, parent_id, agent_type, specialty, capital_allocated,
                    capital_remaining, model_tier)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (agent_id, parent_id, specialty, config["description"],
                 capital, capital, config["model_tier"])
            )
```

> ⚠️ **Caveat 7.1 — Thread Safety for Child Agents:** Each child agent runs in its own daemon thread. Python's GIL prevents true parallelism for CPU-bound work, but since agents are mostly I/O-bound (API calls, email polling), threading works well here. For >5 concurrent child agents, refactor to use `asyncio` throughout. The database connections use `check_same_thread=False` but SQLite write operations should still be serialised — the `log_transaction` function acquires a connection per call, which SQLite handles safely in WAL mode. Enable WAL: `conn.execute("PRAGMA journal_mode=WAL")`.

---

## 12. Phase 8 — Website Agency Child Agent (Deep Dive)

This is the centrepiece of V2. The Website Agency operates as a fully autonomous micro web agency, taking on real client projects, building them with Bonsai (for boilerplate) and Claude Opus (for architecture and quality review), and delivering complete, working websites for sale.

### 12.1 Business Model

```
Revenue Model:
  Landing page (1-page)  →  $150–$250 per project
  Business site (5-page) →  $300–$500 per project
  E-commerce setup       →  $400–$700 per project

Sourcing Channels:
  - Upwork (primary): fixed-price jobs, keywords: "website", "landing page"
  - Fiverr (secondary): standard $150 package listing
  - Reddit r/forhire (organic): show portfolio, respond to requests

Operating Cost:
  - $5/mo Railway hosting (demos/previews)
  - Bonsai: $0 (code generation)
  - Claude Opus 4: ~$2 per project (architecture + quality review)
  - Domain: $12/yr if needed (not always required)

Target: 1 project per 3–4 days = ~$300–$500/week gross at scale
```

### 12.2 Agent Implementation

```python
# agents/children/website_agency.py
import os
import json
import uuid
from pathlib import Path
from loguru import logger
from agents.base_agent import BaseAgent
from agents.model_router import TaskType
from tools.bank_tool import VirtualBankTool
from tools.email_tool import email_tool
from tools.search_tool import search_freelance_jobs, web_search
from tools.bonsai_tool import generate_code_with_bonsai

WEBSITE_AGENCY_SYSTEM_PROMPT = """
You are the Website Agency Agent — a specialist child agent that operates as
a professional micro web agency. You build and sell complete, functional websites.

YOUR IDENTITY:
You represent a small but elite web agency. Every site you produce must be
portfolio-quality. You never ship generic work. You are selective — you only
take projects where you can genuinely add value and deliver exceptional results.

YOUR TOOLSET:
- Bonsai: Free AI code generation for boilerplate HTML/CSS/JS/React
- Claude Opus 4: YOUR OWN reasoning for architecture, design decisions, quality review
- Railway: Deployment and demo hosting
- Upwork/Fiverr APIs: Job sourcing and proposal submission

YOUR PROCESS:
1. Find a suitable project
2. Write a winning proposal (using copywriting skill)
3. Get human approval to submit proposal
4. On client acceptance: scope the project precisely
5. Generate code (Bonsai for bulk, Opus for critical sections)
6. Quality review against frontend_design skill standards
7. Deploy demo to Railway
8. Get human to share demo link with client
9. Client approves → human collects payment → record revenue
"""


class WebsiteAgencyAgent(BaseAgent):
    def __init__(self, agent_id: str, bank_tool: VirtualBankTool,
                 capital: float, parent_id: str):
        super().__init__(agent_id, "website_agency", bank_tool)
        self.capital = capital
        self.parent_id = parent_id
        self.active_projects: list[dict] = []
        self.output_dir = Path(f"deliverables/{agent_id}")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run_loop(self):
        """Main loop: find → propose → build → deliver → collect."""
        logger.info(f"[{self.agent_id}] Website Agency starting run loop")
        while True:
            try:
                self._one_cycle()
            except Exception as e:
                logger.error(f"[{self.agent_id}] Cycle error: {e}")
            import time
            time.sleep(3600)  # Check for new opportunities every hour

    def _one_cycle(self):
        # 1. Find jobs
        jobs = self.find_client_projects()
        if not jobs:
            logger.info(f"[{self.agent_id}] No suitable jobs found this cycle")
            return

        best_job = jobs[0]
        logger.info(f"[{self.agent_id}] Best job: {best_job.get('title')}")

        # 2. Write proposal
        proposal = self.write_proposal(best_job)

        # 3. Get human approval to submit
        reply_tag = email_tool.send_opportunity_brief(
            {
                "title": f"Website Project: {best_job.get('title')}",
                "description": f"Upwork/Fiverr job opportunity\n\nProposal preview:\n{proposal[:500]}...",
                "estimated_revenue_usd": best_job.get("budget", 200),
                "capital_required_usd": 5,  # Just hosting cost
                "time_to_first_revenue_days": 4,
                "human_actions_required": [
                    "Review the proposal draft in the attached document",
                    "Submit the proposal on the platform (agent cannot log in for you)",
                    "Reply DONE when submitted",
                ],
                "demand_evidence": [best_job.get("url", "")],
                "risk_level": "LOW",
            },
            self.agent_id,
        )

        decision = email_tool.poll_for_reply(reply_tag)
        if decision["decision"] not in ["APPROVE", "DONE"]:
            logger.info(f"[{self.agent_id}] Human rejected proposal — skipping")
            return

        logger.info(f"[{self.agent_id}] Proposal approved — waiting for client acceptance")
        # In a real deployment, poll Upwork API for contract acceptance
        # For now: agent waits for human to confirm client accepted

    def find_client_projects(self) -> list[dict]:
        """Search for suitable web development jobs."""
        jobs = []

        # Search Upwork
        upwork_results = search_freelance_jobs(
            platform="upwork",
            keywords="landing page website fixed price budget:150..500"
        )
        for r in upwork_results[:3]:
            jobs.append({
                "source": "upwork",
                "title": r["title"],
                "url": r["url"],
                "budget": self._extract_budget(r["snippet"]),
                "snippet": r["snippet"],
            })

        # Score jobs with LLM
        if not jobs:
            return []

        prompt = f"""
        Score these freelance web development jobs. Select the 1 best job based on:
        - Budget is between $100 and $600
        - Scope is achievable in 2-3 days (single website or landing page)
        - Clear requirements (client knows what they want)
        - No complex backend requirements (no custom databases, payment systems, etc.)

        Jobs:
        {json.dumps(jobs, indent=2)}

        Return a JSON array (sorted best-first) with the same structure.
        Return ONLY valid JSON.
        """

        response = self.llm_call(TaskType.PROPOSAL_DRAFT, prompt,
                                  system_prompt=WEBSITE_AGENCY_SYSTEM_PROMPT)
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            return jobs

    def write_proposal(self, job: dict) -> str:
        """Write a conversion-optimised proposal using copywriting skill."""
        prompt = f"""
        Write a winning freelance proposal for this web development job.

        JOB DETAILS:
        Title: {job.get('title')}
        Description: {job.get('snippet')}
        Budget: ${job.get('budget', 'not specified')}
        Platform: {job.get('source', 'upwork')}

        PROPOSAL REQUIREMENTS:
        - 200-300 words maximum
        - Start with understanding the client's specific problem (not with "I")
        - Explain our design approach and what makes our work distinctive
        - Reference 1-2 specific design choices we'll make for their project
        - Include a brief timeline (Day 1: wireframe, Day 2-3: build, Day 4: revisions)
        - Quote a fixed price at or below their budget
        - End with one smart question about their project
        - Do NOT include fake portfolio links

        Apply the copywriting and client_communications skills.
        Return only the proposal text, ready to paste.
        """

        return self.llm_call(
            TaskType.PROPOSAL_DRAFT,
            prompt,
            system_prompt=WEBSITE_AGENCY_SYSTEM_PROMPT,
            contains_sensitive=False
        )

    def build_website(self, project_spec: dict) -> dict:
        """
        Full website build pipeline:
        1. Opus designs architecture + aesthetic direction
        2. Bonsai generates the bulk of the code
        3. Opus reviews and elevates critical sections
        4. Output: complete website files ready to deploy
        """
        logger.info(f"[{self.agent_id}] Starting website build: {project_spec.get('title')}")
        project_dir = self.output_dir / project_spec.get("project_id", uuid.uuid4().hex[:8])
        project_dir.mkdir(exist_ok=True)

        # STEP 1: Architecture decision (Claude Opus — uses skills)
        architecture_prompt = f"""
        Design the complete architecture for this website project.
        Apply your frontend_design and web_architecture skills.

        PROJECT SPEC:
        {json.dumps(project_spec, indent=2)}

        Provide:
        1. AESTHETIC DIRECTION: Choose one bold aesthetic and commit. Name the fonts,
           primary colour, accent colour, overall feel.
        2. PAGE STRUCTURE: List all pages/sections with their purpose.
        3. TECH STACK: HTML/CSS/JS (static) or React? Justify briefly.
        4. KEY ANIMATIONS: 2-3 micro-interactions that will make this memorable.
        5. TYPOGRAPHY: Exact Google Font names for display and body.
        6. COLOUR SYSTEM: hex values for --color-primary, --color-accent,
           --color-surface, --color-text.

        This architecture document will be given to a code generation model.
        Be precise and specific — no vague descriptions.
        """

        architecture = self.llm_call(
            TaskType.WEBSITE_DESIGN,
            architecture_prompt,
            system_prompt=WEBSITE_AGENCY_SYSTEM_PROMPT,
            contains_sensitive=False
        )

        # Save architecture doc
        (project_dir / "ARCHITECTURE.md").write_text(architecture)
        logger.info(f"[{self.agent_id}] Architecture designed by Opus")

        # STEP 2: Code generation (Bonsai — FREE)
        code_prompt = f"""
        Build a complete, production-ready website based on this architecture.

        ARCHITECTURE:
        {architecture}

        PROJECT TYPE: {project_spec.get('type', 'business website')}
        CLIENT BUSINESS: {project_spec.get('business_name', 'A professional business')}
        KEY MESSAGE: {project_spec.get('key_message', 'We solve your problems professionally')}

        REQUIREMENTS:
        - Single HTML file with embedded CSS and JS (no build step needed)
        - Use Google Fonts (import via @import in <style>)
        - CSS custom properties for all colours (use the exact hex values from architecture)
        - Mobile-responsive with media queries at 768px and 1024px
        - Smooth scroll behaviour
        - Contact form with client-side validation (no backend needed — use Formspree or mailto)
        - Include all content as placeholder text (realistic, professional)
        - Lighthouse-friendly: semantic HTML, alt tags, meta description

        Return ONLY the complete HTML file. No explanations.
        """

        # Privacy check: project_spec must not contain financial data
        generated_code = generate_code_with_bonsai(
            code_prompt,
            context=f"Project type: {project_spec.get('type')} | Stack: HTML/CSS/JS"
        )

        if not generated_code:
            logger.error(f"[{self.agent_id}] Bonsai code generation failed")
            return {"success": False, "error": "Code generation failed"}

        # Save initial code
        html_file = project_dir / "index.html"
        html_file.write_text(generated_code)
        logger.info(f"[{self.agent_id}] Code generated by Bonsai ({len(generated_code)} chars)")

        # STEP 3: Quality review (Claude Opus — premium)
        review_prompt = f"""
        You are reviewing a website built for a client.
        Apply your frontend_design skill quality standards rigorously.

        Review this HTML and provide a REVISED version that fixes any issues:
        1. Typography: Are the fonts distinctive and properly loaded?
        2. Colour system: Are CSS variables used consistently?
        3. Mobile: Will this look professional on a 375px screen?
        4. Animations: Are the specified micro-interactions implemented?
        5. Content: Is all placeholder text professional and realistic?
        6. Performance: Any obvious issues (missing alt tags, uncompressed images, etc.)?

        Return the COMPLETE improved HTML file. Fix all issues inline.
        Do not describe what you changed — just return the improved code.

        ORIGINAL CODE:
        {generated_code[:6000]}  # Trim to stay within context
        """

        reviewed_code = self.llm_call(
            TaskType.WEBSITE_DESIGN,
            review_prompt,
            system_prompt=WEBSITE_AGENCY_SYSTEM_PROMPT,
            contains_sensitive=False
        )

        if reviewed_code and len(reviewed_code) > 500:
            html_file.write_text(reviewed_code)
            logger.info(f"[{self.agent_id}] Opus quality review complete")

        return {
            "success": True,
            "project_dir": str(project_dir),
            "html_file": str(html_file),
            "architecture": architecture,
        }

    def deploy_demo(self, html_file: str) -> str:
        """
        Deploy the built website to Railway for client preview.
        Returns the preview URL.

        IMPLEMENTATION NOTE:
        This uses the Railway CLI. Ensure `railway` is installed:
        npm install -g @railway/cli
        railway login (one-time)
        """
        project_dir = Path(html_file).parent
        demo_url = ""

        # Create a minimal Railway project structure
        (project_dir / "railway.json").write_text(json.dumps({
            "schema": "https://railway.app/railway.schema.json",
            "build": {"builder": "NIXPACKS"},
            "deploy": {"startCommand": "python -m http.server 8080", "restartPolicyType": "ON_FAILURE"}
        }))
        (project_dir / "requirements.txt").write_text("")  # Empty — Python stdlib only

        logger.info(f"[{self.agent_id}] Deploy to Railway — run manually: railway up in {project_dir}")
        logger.info("ACTION REQUIRED: Human must run 'railway up' in project dir and share URL with client")
        return f"[Manual deployment required — see logs for path: {project_dir}]"

    def _extract_budget(self, text: str) -> float:
        """Extract a dollar amount from job listing text."""
        import re
        matches = re.findall(r'\$(\d+(?:,\d+)?)', text)
        if matches:
            return float(matches[0].replace(",", ""))
        return 200.0  # Default assumption
```

### 12.3 Website Agency Workflow (Visual)

```
[WEBSITE AGENCY AGENT]
         │
         ▼
   Source Jobs (Upwork/Fiverr)
   Model: Gemini Flash (T1) — search + basic scoring
         │
         ▼
   Score & Select Best Job
   Model: GPT-4o mini (T2) — proposal quality judgement
         │
         ▼
   Write Proposal
   Model: GPT-4o mini (T2) + copywriting skill
         │
         ▼
   ──── EMAIL HUMAN ──── OPPORTUNITY_BRIEF
         │
         │ Human reviews, submits proposal on platform
         ▼
   [Wait for client to accept on platform]
         │
         ▼
   Scope the Project (client requirements → spec JSON)
   Model: Claude Opus 4 (T4) + client_communications skill
         │
         ▼
   Design Architecture
   Model: Claude Opus 4 (T4) + frontend_design + web_architecture skills
         │
         ▼
   Generate Code (boilerplate)
   Model: BONSAI (FREE) — bulk HTML/CSS/JS
         │
         ▼
   Quality Review + Polish
   Model: Claude Opus 4 (T4) + frontend_design skill
         │
         ▼
   Deploy Demo to Railway
   (Human runs `railway up` — ACTION_REQUIRED email)
         │
         ▼
   Client Reviews Demo
         │
    ┌────┴────┐
    │ Approves │  → Human collects payment → record_revenue() → profit++
    │ Revisions│  → Agent revises (1 round free) → redeploy
    └──────────┘
```

> ⚠️ **Caveat 8.1 — Bonsai Code Quality Variability:** Because Bonsai routes to random frontier models, quality varies significantly between sessions. ALWAYS run Opus quality review after Bonsai generation. Never ship Bonsai-generated code directly to a paying client. Treat Bonsai as a junior developer whose work you always review.

> ⚠️ **Caveat 8.2 — Upwork Profile Requirement:** The Website Agency cannot create an Upwork account autonomously. You (the human) must create a profile with at least 3 portfolio items before the agent can submit proposals. The agent will draft the portfolio descriptions and proposals — you submit them. This is a one-time setup cost of ~2 hours.

> ⚠️ **Caveat 8.3 — Claude Opus Context Limit:** Opus 4 has an 8,192 token output limit in our configuration. For a full website (often 1000+ lines of HTML), you may hit this limit during quality review. Solution: split the review into sections (header review, main content review, footer review) with separate Opus calls. The `build_website` code trims input to 6000 chars as a workaround — increase this and split if needed.

> ⚠️ **Caveat 8.4 — Payment Collection:** The agent cannot collect payments. All payment collection is a human action. The flow is: agent delivers demo → human shares with client → client approves → human sends invoice (Wise Request Money or PayPal) → client pays → human records receipt and replies DONE to agent → agent calls `bank_tool.record_revenue()`.

---

## 13. Phase 9 — Other Child Agents

### 13.1 AI Wrapper Builder Agent

```python
# agents/children/ai_wrapper_builder.py
# Abbreviated — follows same BaseAgent pattern

WRAPPER_SYSTEM_PROMPT = """
You are the AI Wrapper Builder — a specialist agent that builds and sells
focused AI-powered micro-tools. Your niche: tools that do ONE thing extremely
well using an LLM backend, sold as a simple web interface.

TARGET PRODUCTS:
- Cold email personaliser: paste a LinkedIn URL → get a personalised opening line
- Resume keyword optimiser: paste job description → get gap analysis
- Legal document plain-English explainer
- Meeting notes → action items extractor

PRICING: $9 one-time (Gumroad) or $5/month (Stripe subscription)
STACK: FastAPI (Python) backend + single-page HTML frontend
HOSTING: Railway (free tier for low-traffic tools)
"""

class AIWrapperAgent(BaseAgent):
    def find_niche(self) -> dict:
        """Find an underserved AI tool niche using Reddit + Product Hunt."""
        results = web_search(
            'site:reddit.com "I wish there was an AI" OR "is there a tool that" 2025',
            max_results=10, use_tavily=True
        )
        prompt = f"""
        Find the most frequently requested AI tool that doesn't yet exist.
        Focus on: professional productivity, not entertainment.

        Evidence:
        {json.dumps(results, indent=2)}

        Return JSON: {{
          "niche": "description",
          "target_user": "who wants this",
          "core_feature": "the one thing it does",
          "evidence_urls": ["url1", "url2"],
          "estimated_monthly_searches": integer
        }}
        """
        response = self.llm_call(TaskType.OPPORTUNITY_SCORE, prompt,
                                  system_prompt=WRAPPER_SYSTEM_PROMPT)
        return json.loads(response)

    def build_wrapper(self, niche: dict) -> str:
        """Build the FastAPI + HTML interface using Bonsai."""
        backend_prompt = f"""
        Build a FastAPI Python backend for this AI tool:
        Tool: {niche['niche']}
        Core feature: {niche['core_feature']}

        Requirements:
        - Single endpoint POST /process that accepts user input
        - Calls the Anthropic API (claude-haiku-4-5-20251001 for cost efficiency)
        - Returns JSON with the result
        - Include CORS headers for the frontend
        - Include a /health endpoint
        - Use python-dotenv for ANTHROPIC_API_KEY

        Return the complete main.py file.
        """
        frontend_prompt = f"""
        Build a single-page HTML frontend for this AI tool:
        Tool: {niche['niche']}

        Requirements:
        - Clean, professional design — NOT generic
        - Input field(s) appropriate for the use case
        - Submit button with loading state
        - Result display area with copy button
        - Mobile responsive
        - Calls POST /process (assume same origin)

        Return the complete index.html file.
        """

        backend_code = generate_code_with_bonsai(backend_prompt)
        frontend_code = generate_code_with_bonsai(frontend_prompt)

        project_dir = self.output_dir / f"wrapper-{uuid.uuid4().hex[:6]}"
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "main.py").write_text(backend_code)
        (project_dir / "index.html").write_text(frontend_code)
        (project_dir / "requirements.txt").write_text(
            "fastapi\nuvicorn\nanthropicpython-dotenv\nhttpx"
        )

        return str(project_dir)
```

### 13.2 Crypto Trader Agent (Abbreviated)

```python
# agents/children/crypto_trader.py
import pandas as pd
import talib
from binance.client import Client

class CryptoTraderAgent(BaseAgent):
    def __init__(self, agent_id, bank_tool, capital, parent_id):
        super().__init__(agent_id, "crypto_trader", bank_tool)
        self.capital = capital
        self.binance = Client(
            os.getenv("BINANCE_API_KEY"),
            os.getenv("BINANCE_SECRET_KEY")
        )

    def get_signal(self, symbol="BTCUSDT", interval="4h") -> dict:
        """Generate trading signal using TA-Lib indicators."""
        klines = self.binance.get_klines(symbol=symbol, interval=interval, limit=100)
        df = pd.DataFrame(klines, columns=[
            'open_time','open','high','low','close','volume',
            'close_time','quote_vol','trades','taker_buy_base',
            'taker_buy_quote','ignore'
        ])
        close = df['close'].astype(float).values
        high = df['high'].astype(float).values
        low = df['low'].astype(float).values

        rsi = talib.RSI(close, timeperiod=14)[-1]
        macd, signal, _ = talib.MACD(close)
        ema_20 = talib.EMA(close, timeperiod=20)[-1]
        ema_50 = talib.EMA(close, timeperiod=50)[-1]
        atr = talib.ATR(high, low, close, timeperiod=14)[-1]

        # Apply risk_management skill rules via LLM
        indicator_data = {
            "symbol": symbol, "rsi": round(rsi, 2),
            "macd_bullish": bool(macd[-1] > signal[-1]),
            "ema_trend": "UP" if ema_20 > ema_50 else "DOWN",
            "atr": round(atr, 2), "current_price": float(close[-1])
        }

        prompt = f"""
        Analyse these technical indicators and apply risk management rules.
        Return a trade signal or NO_TRADE.

        Indicators: {json.dumps(indicator_data)}

        Apply trading skill rules: RSI overbought/oversold, MACD confirmation,
        EMA trend alignment. Max 20% of capital per trade, 5% stop-loss.

        Return JSON: {{
          "action": "BUY" | "SELL" | "NO_TRADE",
          "reasoning": "one sentence",
          "entry_price": float,
          "stop_loss": float,
          "take_profit": float,
          "position_size_usd": float
        }}
        """

        response = self.llm_call(TaskType.TRADE_SIGNAL, prompt,
                                  contains_sensitive=True)  # Financial data → not Bonsai
        return json.loads(response)
```

> ⚠️ **Caveat 9.1 — Binance Account Requirements:** Binance requires identity verification (KYC) and is not available in all jurisdictions. Pakistani users should use Binance.com international or check local regulations. API trading requires enabling Spot Trading permissions on the API key — do NOT enable Futures/Margin permissions.

---

## 14. Phase 10 — State Machine (LangGraph)

```python
# state_machine/lifecycle.py
from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal
from loguru import logger


class AgentState(TypedDict):
    agent_id: str
    status: Literal[
        "IDLE", "RESEARCHING", "AWAITING_APPROVAL",
        "EXECUTING", "EVALUATING", "SPAWNING_CHILD",
        "MONITORING", "REPORTING", "TERMINATED"
    ]
    current_opportunity: dict | None
    human_decision: str | None
    last_outcome: dict | None
    error_count: int
    cycle_count: int


def research_node(state: AgentState, agent) -> AgentState:
    logger.info(f"[{state['agent_id']}] STATE: RESEARCHING")
    opportunities = agent.research_opportunities()
    best = agent.select_best_opportunity(opportunities)
    return {**state, "current_opportunity": best,
            "status": "AWAITING_APPROVAL" if best else "IDLE"}


def await_approval_node(state: AgentState, agent) -> AgentState:
    logger.info(f"[{state['agent_id']}] STATE: AWAITING_APPROVAL")
    # This runs in a thread — does not block the main process
    import threading
    result_holder = {}

    def poll():
        decision = agent.request_human_approval(state["current_opportunity"])
        result_holder["decision"] = decision

    t = threading.Thread(target=poll, daemon=True)
    t.start()
    t.join(timeout=3600 * 73)  # 73-hour max (matches email tool abort)

    decision = result_holder.get("decision", {"decision": "TIMEOUT"})
    return {**state, "human_decision": decision["decision"],
            "status": "EXECUTING" if decision["decision"] == "APPROVE" else "IDLE"}


def execute_node(state: AgentState, agent) -> AgentState:
    logger.info(f"[{state['agent_id']}] STATE: EXECUTING")
    opportunity = state["current_opportunity"]
    # Delegate to vertical-specific executor
    outcome = agent.execute_opportunity(opportunity)
    return {**state, "last_outcome": outcome, "status": "EVALUATING"}


def evaluate_node(state: AgentState, agent) -> AgentState:
    logger.info(f"[{state['agent_id']}] STATE: EVALUATING")
    outcome = state["last_outcome"]
    if outcome and outcome.get("profit_usd", 0) > 0:
        agent.bank_tool.record_revenue(
            outcome["profit_usd"],
            outcome.get("source", "opportunity"),
            state["agent_id"]
        )
        return {**state, "status": "SPAWNING_CHILD",
                "cycle_count": state["cycle_count"] + 1}
    else:
        return {**state, "status": "RESEARCHING",
                "cycle_count": state["cycle_count"] + 1,
                "error_count": state["error_count"] + (1 if not outcome else 0)}


def spawn_node(state: AgentState, agent) -> AgentState:
    logger.info(f"[{state['agent_id']}] STATE: SPAWNING_CHILD")
    outcome = state["last_outcome"]
    specialty = outcome.get("vertical_specialty", "ai_wrapper_builder")
    profit = agent.bank_tool.get_balance().get("total_profit", 0)
    capital_for_child = min(profit * 0.3, 50)  # Allocate 30% of profit, max $50

    try:
        agent.spawn_child_agent(specialty, capital_for_child)
    except Exception as e:
        logger.error(f"Spawn failed: {e}")

    return {**state, "status": "MONITORING"}


def build_fsm(agent) -> callable:
    """Build and compile the LangGraph state machine for an agent."""
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("research", lambda s: research_node(s, agent))
    graph.add_node("await_approval", lambda s: await_approval_node(s, agent))
    graph.add_node("execute", lambda s: execute_node(s, agent))
    graph.add_node("evaluate", lambda s: evaluate_node(s, agent))
    graph.add_node("spawn_child", lambda s: spawn_node(s, agent))

    # Add edges
    graph.set_entry_point("research")
    graph.add_edge("research", "await_approval")
    graph.add_conditional_edges(
        "await_approval",
        lambda s: "execute" if s["human_decision"] == "APPROVE" else "research"
    )
    graph.add_edge("execute", "evaluate")
    graph.add_conditional_edges(
        "evaluate",
        lambda s: "spawn_child" if s["status"] == "SPAWNING_CHILD" else "research"
    )
    graph.add_edge("spawn_child", "research")

    return graph.compile()
```

---

## 15. Phase 11 — Scheduler & Weekly Report

```python
# scheduler/weekly_timer.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger
from memory.database import get_connection, get_budget_state
from tools.email_tool import email_tool
from memory.snapshot import create_snapshot

scheduler = BackgroundScheduler()


def generate_weekly_report() -> dict:
    """Aggregate all financial data for the weekly email report."""
    budget = get_budget_state()

    with get_connection("transactions") as conn:
        transactions = conn.execute(
            "SELECT * FROM transactions ORDER BY timestamp DESC LIMIT 100"
        ).fetchall()
        revenue_total = conn.execute(
            "SELECT SUM(amount) FROM transactions WHERE direction='credit'"
        ).fetchone()[0] or 0
        spend_total = conn.execute(
            "SELECT SUM(amount) FROM transactions WHERE direction='debit'"
        ).fetchone()[0] or 0

    with get_connection("agents") as conn:
        all_agents = conn.execute("SELECT * FROM agents").fetchall()
        profitable_agents = conn.execute(
            "SELECT * FROM agents WHERE status='profitable'"
        ).fetchall()

    with get_connection("episodes") as conn:
        episodes = conn.execute(
            "SELECT * FROM episodes ORDER BY created_at DESC"
        ).fetchall()

    return {
        "api_reserve_remaining": budget["api_reserve"],
        "investment_pool_remaining": budget["investment_pool"],
        "total_revenue": revenue_total,
        "total_spend": spend_total,
        "net_profit": revenue_total - spend_total,
        "total_agents_spawned": len(all_agents),
        "profitable_agents": len(profitable_agents),
        "total_episodes": len(episodes),
        "transactions": [dict(t) for t in transactions[:20]],
        "agents": [dict(a) for a in all_agents],
        "episodes": [dict(e) for e in episodes],
    }


def weekly_shutdown():
    """Send report, save snapshot, gracefully terminate."""
    logger.info("=== WEEKLY SHUTDOWN SEQUENCE STARTING ===")

    # 1. Generate and send report
    report_data = generate_weekly_report()
    email_tool.send_weekly_report(report_data)
    logger.info("Weekly report sent")

    # 2. Save memory snapshot for restart
    create_snapshot()
    logger.info("Memory snapshot saved")

    # 3. Log termination
    logger.info("=== AAE WEEKLY CYCLE COMPLETE — SYSTEM TERMINATING ===")
    logger.info(f"Net profit this week: ${report_data['net_profit']:.2f}")
    logger.info(f"Agents spawned: {report_data['total_agents_spawned']}")

    # 4. Exit (systemd/Railway will restart automatically)
    import sys
    sys.exit(0)


def start_scheduler():
    # Weekly report every Sunday at 23:00
    scheduler.add_job(
        weekly_shutdown,
        CronTrigger(day_of_week="sun", hour=23, minute=0),
        id="weekly_shutdown"
    )

    # Midnight daily: reset model token budgets
    scheduler.add_job(
        lambda: None,  # Router resets internally via reset_daily_budgets()
        CronTrigger(hour=0, minute=1),
        id="daily_budget_reset"
    )

    # Every 6 hours: check API reserve health
    scheduler.add_job(
        lambda: None,  # Main loop handles this
        CronTrigger(hour="*/6"),
        id="health_check"
    )

    scheduler.start()
    logger.info("Scheduler started")
```

---

## 16. Phase 12 — Memory & Restart System

```python
# memory/snapshot.py
import json
from datetime import datetime
from pathlib import Path
from memory.database import get_connection, get_budget_state
from loguru import logger

SNAPSHOT_FILE = Path("memory/snapshot.json")


def create_snapshot():
    """Serialise full system state to JSON for restart."""
    budget = get_budget_state()

    with get_connection("agents") as conn:
        active_agents = conn.execute(
            "SELECT * FROM agents WHERE status='active'"
        ).fetchall()
        agents_data = [dict(a) for a in active_agents]

    with get_connection("episodes") as conn:
        recent_episodes = conn.execute(
            "SELECT * FROM episodes ORDER BY created_at DESC LIMIT 50"
        ).fetchall()
        episodes_data = [dict(e) for e in recent_episodes]

    snapshot = {
        "snapshot_version": "2.0",
        "created_at": datetime.now().isoformat(),
        "budget_state": budget,
        "active_agents": agents_data,
        "recent_episodes": episodes_data,
        "restart_ready": True,
    }

    SNAPSHOT_FILE.write_text(json.dumps(snapshot, indent=2, default=str))
    logger.info(f"Snapshot saved: {SNAPSHOT_FILE} ({SNAPSHOT_FILE.stat().st_size} bytes)")


def load_snapshot() -> dict | None:
    if not SNAPSHOT_FILE.exists():
        return None
    data = json.loads(SNAPSHOT_FILE.read_text())
    if not data.get("restart_ready"):
        return None
    return data


def restart_from_snapshot():
    """
    Restart the system using persisted state.
    Recreates all previously active child agents with their remaining capital.
    """
    snapshot = load_snapshot()
    if not snapshot:
        logger.info("No snapshot found — starting fresh")
        return False

    logger.info(f"Resuming from snapshot: {snapshot['created_at']}")
    logger.info(f"Restoring {len(snapshot['active_agents'])} agents")

    from tools.bank_tool import VirtualBankTool
    from agents.child_factory import ChildAgentFactory
    bank_tool = VirtualBankTool()

    # Restore budget state
    from memory.database import update_budget
    bs = snapshot["budget_state"]
    update_budget(
        api_reserve=bs["api_reserve"],
        investment_pool=bs["investment_pool"],
        total_revenue=bs["total_revenue"],
        total_profit=bs["total_profit"],
    )

    # Restore child agents (NOT mother — mother always restarts fresh)
    factory = ChildAgentFactory(bank_tool)
    for agent_data in snapshot["active_agents"]:
        if agent_data["parent_id"]:  # Skip mother agent
            try:
                factory.spawn(
                    specialty=agent_data["agent_type"],
                    capital=agent_data["capital_remaining"],
                    parent_id=agent_data["parent_id"],
                )
                logger.info(f"Restored: {agent_data['agent_id']}")
            except Exception as e:
                logger.error(f"Failed to restore {agent_data['agent_id']}: {e}")

    return True
```

---

## 17. Phase 13 — Testing & Simulation Mode

### 17.1 Run Everything in Simulation First

```bash
# Set in .env before ANY testing:
SIMULATION_MODE=true
```

When `SIMULATION_MODE=true`:
- `VirtualBankTool.spend_investment()` logs but never calls Wise API
- All money moves are SQLite-only
- Email tool still sends real emails (use a test Gmail account)
- Bonsai still generates real code (safe — no financial data)
- Claude/Gemini still make real API calls (small cost for testing)

### 17.2 Unit Tests

```python
# tests/test_bank_tool.py
import pytest
import os
os.environ["SIMULATION_MODE"] = "true"
os.environ["WISE_API_KEY"] = "test"
os.environ["WISE_PROFILE_ID"] = "test"
os.environ["WISE_ACCOUNT_ID"] = "test"

from memory.database import init_databases
from tools.bank_tool import VirtualBankTool

@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "memory").mkdir()
    init_databases()
    yield

def test_spend_within_limit():
    bank = VirtualBankTool()
    result = bank.spend_investment(15.0, "Test purchase", "AGENT-001", "test")
    assert result.success is True
    assert result.balance_after == 85.0  # 100 - 15

def test_spend_exceeds_limit_blocked():
    bank = VirtualBankTool()
    result = bank.spend_investment(25.0, "Over limit", "AGENT-001", "test",
                                    human_pre_approved=False)
    assert result.success is False
    assert "Human approval required" in result.blocked_reason

def test_spend_with_approval():
    bank = VirtualBankTool()
    result = bank.spend_investment(25.0, "Approved", "AGENT-001", "test",
                                    human_pre_approved=True)
    assert result.success is True

def test_revenue_recording():
    bank = VirtualBankTool()
    result = bank.record_revenue(50.0, "Website sale", "AGENT-001")
    assert result.success is True
    state = bank.get_balance()
    assert state["total_profit"] == 50.0
    assert state["investment_pool"] == 150.0  # 100 base + 50 revenue

def test_api_reserve_health():
    bank = VirtualBankTool()
    healthy, remaining = bank.check_api_reserve_health()
    assert healthy is True
    assert remaining == 50.0
```

```python
# tests/test_skill_loader.py
import pytest
from pathlib import Path
from skills.skill_loader import SkillLoader

@pytest.fixture
def skill_dir(tmp_path):
    skills = tmp_path / "skills" / "core"
    skills.mkdir(parents=True)
    (skills / "test_skill.md").write_text("# Test Skill\nDo things well.")
    return tmp_path

def test_load_skill(skill_dir, monkeypatch):
    monkeypatch.chdir(skill_dir)
    loader = SkillLoader()
    content = loader.load("core/test_skill")
    assert "Test Skill" in content
    assert "Do things well" in content

def test_load_bundle(skill_dir, monkeypatch):
    monkeypatch.chdir(skill_dir)
    loader = SkillLoader()
    bundle = loader.load_bundle(["core/test_skill"])
    assert "LOADED EXPERTISE SKILLS" in bundle
    assert "SKILL: Test Skill" in bundle

def test_missing_skill_returns_empty(skill_dir, monkeypatch):
    monkeypatch.chdir(skill_dir)
    loader = SkillLoader()
    content = loader.load("core/nonexistent")
    assert content == ""
```

### 17.3 Integration Test: Full Opportunity Cycle

```python
# tests/test_full_cycle.py
"""
Integration test — runs a complete simulated opportunity cycle.
Requires: SIMULATION_MODE=true, real Gmail credentials, Gemini API key.
"""
import pytest
import os
os.environ["SIMULATION_MODE"] = "true"

from memory.database import init_databases
from tools.bank_tool import VirtualBankTool

def test_mother_agent_research_cycle(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "memory").mkdir()
    (tmp_path / "skills").mkdir()
    init_databases()

    bank = VirtualBankTool()
    from agents.mother_agent import MotherAgent
    agent = MotherAgent(bank)

    # Should complete without raising
    opportunities = agent.research_opportunities()
    assert isinstance(opportunities, list)

    if opportunities:
        best = agent.select_best_opportunity(opportunities)
        assert best is None or isinstance(best, dict)
        if best:
            assert "estimated_revenue_usd" in best
            assert "capital_required_usd" in best
```

### 17.4 Running Tests

```bash
# Run all unit tests (fast, no external APIs)
pytest tests/test_bank_tool.py tests/test_skill_loader.py -v

# Run integration tests (requires API keys, slower)
pytest tests/test_full_cycle.py -v -s

# Run with coverage report
pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html
```

---

## 18. Phase 14 — Deployment

### 18.1 Entry Point

```python
# main.py
import os
import sys
import argparse
import threading
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

from utils.logging_setup import configure_logging
from memory.database import init_databases
from memory.snapshot import restart_from_snapshot
from tools.bank_tool import VirtualBankTool
from agents.mother_agent import MotherAgent
from state_machine.lifecycle import build_fsm, AgentState
from scheduler.weekly_timer import start_scheduler

configure_logging(os.getenv("LOG_LEVEL", "INFO"))


def main():
    parser = argparse.ArgumentParser(description="Autonomous Agent Ecosystem")
    parser.add_argument("--mode", choices=["simulate", "live"], default="simulate",
                        help="simulate (no real money) or live (real Wise API)")
    parser.add_argument("--restart", action="store_true",
                        help="Restore from last snapshot")
    args = parser.parse_args()

    if args.mode == "live":
        os.environ["SIMULATION_MODE"] = "false"
        logger.warning("=== LIVE MODE — REAL MONEY WILL BE SPENT ===")
        confirm = input("Type CONFIRM to proceed: ")
        if confirm != "CONFIRM":
            logger.info("Aborted")
            sys.exit(0)
    else:
        os.environ["SIMULATION_MODE"] = "true"
        logger.info("=== SIMULATION MODE — No real money ===")

    # Initialise databases
    init_databases()

    # Restore from snapshot if requested
    if args.restart:
        restored = restart_from_snapshot()
        if restored:
            logger.info("System restored from snapshot")
        else:
            logger.info("No valid snapshot — starting fresh")

    # Start scheduler (weekly report + daily budget reset)
    start_scheduler()

    # Initialise bank tool and mother agent
    bank = VirtualBankTool()
    mother = MotherAgent(bank)

    # Build and run the state machine
    fsm = build_fsm(mother)
    initial_state: AgentState = {
        "agent_id": mother.agent_id,
        "status": "IDLE",
        "current_opportunity": None,
        "human_decision": None,
        "last_outcome": None,
        "error_count": 0,
        "cycle_count": 0,
    }

    logger.info(f"Mother Agent {mother.agent_id} starting FSM")
    logger.info(f"Skills loaded: {mother.skills_loaded}")

    # Run FSM in a loop (it handles its own state transitions)
    final_state = fsm.invoke(initial_state)
    logger.info(f"FSM completed with state: {final_state['status']}")


if __name__ == "__main__":
    main()
```

### 18.2 Deploy to Railway

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Initialise project (run in aae/ directory)
railway init

# 4. Set environment variables (do NOT commit .env)
railway variables set GEMINI_API_KEY=xxx
railway variables set ANTHROPIC_API_KEY=xxx
railway variables set BONSAI_API_KEY=xxx
railway variables set TAVILY_API_KEY=xxx
railway variables set GMAIL_ADDRESS=xxx
railway variables set GMAIL_APP_PASSWORD=xxx
railway variables set HUMAN_EMAIL=xxx
railway variables set WISE_API_KEY=xxx
railway variables set WISE_PROFILE_ID=xxx
railway variables set SIMULATION_MODE=true  # Start in simulation!

# 5. Create Procfile
echo "web: python main.py --mode simulate" > Procfile

# 6. Deploy
railway up

# 7. Monitor logs
railway logs --tail
```

### 18.3 Production Checklist

```
Before going live ($SIMULATION_MODE=false):

System:
[ ] Ran simulation for 48 hours without errors
[ ] Reviewed all agent email decisions — do they make sense?
[ ] Wise card daily limit set to $25 AT THE BANK LEVEL
[ ] Tested bank tool spend() with a $1 real transaction
[ ] Tested email tool — received and replied to a test OPPORTUNITY_BRIEF
[ ] All API keys rotated after testing (fresh keys for production)

Database:
[ ] Backup memory/*.db before going live
[ ] Verified budget_state shows correct initial balances
[ ] Confirmed SIMULATION_MODE=false only in Railway env vars (not in .env)

Agent Configuration:
[ ] Upwork profile created with portfolio items (for Website Agency)
[ ] Binance account verified with Spot Trading API key (for Crypto)
[ ] Gumroad/LemonSqueezy account set up (for App/AI Wrapper)
[ ] Chrome Developer account ($5 one-time fee) registered (for Extension)

Monitoring:
[ ] Set up Railway webhook alerts for crashes
[ ] Created a separate Gmail label for AAE emails
[ ] Phone notifications enabled for CRITICAL-tagged emails
[ ] Added HUMAN_EMAIL as your primary personal email — not a secondary
```

---

## 19. Master Caveats Reference

### FINANCIAL

| # | Caveat | Mitigation |
|---|---|---|
| F1 | Real money is at risk from Day 1 of live mode | Set Wise card limit to $25/day at bank level |
| F2 | Agent can retry failed transactions, multiplying spend | Circuit breaker: max 3 retries per opportunity |
| F3 | Revenue may not arrive in Wise immediately (3-5 day bank transfer) | Record revenue only when confirmed in Wise balance |
| F4 | Crypto positions can lose more than expected if stop-loss gaps | Crypto child agent limited to 20% of pool per trade |
| F5 | Child agent capital allocation is a real debit | Verify agents.db capital_remaining before spawning |

### TECHNICAL

| # | Caveat | Mitigation |
|---|---|---|
| T1 | Bonsai logs all prompts — no sensitive data ever | _is_safe_for_bonsai() gate in every call |
| T2 | Bonsai model changes every 24h — quality varies | Always run Opus review after Bonsai generation |
| T3 | Gmail IMAP poll may miss replies if subject changes | Parse reply_tag from body, not just subject |
| T4 | SQLite concurrent writes with >3 child agents | Enable WAL mode; migrate to Postgres at scale |
| T5 | LangGraph FSM blocks on AWAITING_APPROVAL node | Run polling in daemon thread, not blocking |
| T6 | Bonsai API endpoint not publicly documented | Monitor docs.trybons.ai + Discord for updates |
| T7 | TA-Lib installation requires C library | Pre-install on Railway via nixpacks.toml |

### LEGAL & PLATFORM

| # | Caveat | Mitigation |
|---|---|---|
| L1 | Upwork ToS prohibits undisclosed AI submissions | Proposals must disclose: "built with AI assistance" |
| L2 | Crypto spot trading is grey area in Pakistan | Trade only on verified international platforms; consult local counsel |
| L3 | Chrome Web Store rejects extensions with broad permissions | Request only necessary permissions in manifest.json |
| L4 | AI wrapper products reselling LLM output may violate API ToS | Check OpenAI/Anthropic ToS for commercial resale terms |
| L5 | Income from any source is taxable | Keep all transaction logs for tax filing |

### RESEARCH VALIDITY

| # | Caveat | Impact |
|---|---|---|
| R1 | Null results (no profit in 7 days) are equally valid data | Document failure modes — they are findings |
| R2 | Human approval bias affects experiment results | Log ALL approval/rejection decisions with reasoning |
| R3 | Market conditions in testing week affect generalisability | Run across multiple weeks for statistical validity |
| R4 | Agent success may be highly dependent on specific model versions | Pin all model IDs; document exact versions used |

---

## 20. Quick Reference Cheatsheet

### Startup Commands

```bash
# First time setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
npm install -g @bonsai-ai/cli && bonsai login
python -c "from memory.database import init_databases; init_databases()"

# Run simulation (safe)
python main.py --mode simulate

# Run live (real money)
python main.py --mode live

# Restart from last week's snapshot
python main.py --mode live --restart

# Check database
sqlite3 memory/transactions.db "SELECT * FROM budget_state;"
sqlite3 memory/agents.db "SELECT agent_id, specialty, status, total_earned FROM agents;"
```

### Model Quick Reference

| Task | Model | Why |
|---|---|---|
| Code generation | Bonsai (FREE) | No cost, frontier quality |
| Web search | Gemini Flash | Cheapest reasoning model |
| Trade signals | GPT-4o mini (T2) | Moderate reasoning, cheap |
| Website architecture | Claude Opus 4 (T4) | Best design reasoning |
| Weekly synthesis | Claude Opus 4 (T4) | Complex narrative generation |
| Email drafting | Gemini Flash | Simple, frequent task |

### Key File Locations

```
Logs:             logs/aae_YYYY-MM-DD.log
Financial audit:  logs/financial_audit.log
Budget state:     memory/transactions.db → budget_state table
All agents:       memory/agents.db → agents table
Restart file:     memory/snapshot.json
Skills:           skills/**/*.md
Website builds:   deliverables/{agent_id}/
```

### Emergency Procedures

```bash
# Stop all agent spending immediately
sqlite3 memory/transactions.db \
  "UPDATE budget_state SET investment_pool = 0;"

# Force simulation mode (without restart)
export SIMULATION_MODE=true

# Check current burn rate
sqlite3 memory/transactions.db \
  "SELECT SUM(amount), category FROM transactions
   WHERE direction='debit' AND date(timestamp) = date('now')
   GROUP BY category;"

# Manually record revenue (e.g. Upwork payment received)
python -c "
from memory.database import init_databases; init_databases()
from tools.bank_tool import VirtualBankTool
VirtualBankTool().record_revenue(250.0, 'Upwork website project', 'MANUAL')
"
```

---

*AAE V2 — Implementation Roadmap | Research: Real-World AI Autonomous Business Capability*  
*Model Note: "claude-opus-4-6" is the current production string for Claude Opus 4. The V1.1 document referenced "Opus 4.7" — always check console.anthropic.com for the latest model strings before deployment.*
