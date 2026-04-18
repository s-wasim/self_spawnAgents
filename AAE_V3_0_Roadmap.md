# Autonomous Agent Ecosystem (AAE) — V3.0 Implementation Roadmap

> **Status:** FINAL, authoritative specification for end-to-end implementation by a coding agent (Claude Code or equivalent).
> **Date:** 2026-04-18
> **Supersedes:** V1.1, V2, V2.2. This document stands alone; prior drafts are archival.
> **Target implementer:** An autonomous coding agent with filesystem, shell, and git access.

---

## 0. What V3.0 Is (one-page summary)

V3.0 is a **four-agent, zero-human-touch autonomous revenue system** that an operator can launch from a single Hetzner VPS (or Railway Pro) with a one-time day-0 setup. After Day 0, the operator's only duties are: (a) clicking APPROVE/REJECT on emailed `VerticalProposal` objects, and (b) replying CONTINUE / PAUSE / KILL to the weekly digest.

The four agents:

1. **Mother Agent** — stateful LangGraph controller; holds long-term memory (Postgres + pgvector), owns the three-pot cashflow ledger, proposes new verticals, writes pre-registration specs, dispatches Code Builder jobs, monitors Child agents, generates weekly digests, and requests human approval only at defined gates.
2. **Code Builder Agent** — stateless; receives a `BuildRequest`, writes Python tool code, runs it in a hardened Docker sandbox (network=none, read-only rootfs, 512 MB, 1 CPU, 5-minute wall clock, gVisor runtime on Hetzner), validates with pytest, and returns a signed `ToolArtifact` or a `BuildFailure`.
3. **Ethics Auditor Agent** — stateless, profit-blind, fixed-tier (Claude Opus 4.7, no memory, no tool access, no retry on its own verdicts). Reviews every `VerticalProposal` and every high-risk `ToolArtifact` before they reach the human. Produces an `EthicsVerdict{APPROVE | REJECT | ESCALATE, rationale}`. Its prompt is in `FROZEN_PATHS` — any edit trips the integrity alarm.
4. **Child Agents** — one per approved vertical. Each is a restricted LangGraph instance bound to a single revenue channel (from the allowlist in §6), with a capped monthly budget, a frozen product spec, and a pre-registered success metric. Children cannot spawn children. Children cannot add payment rails. Children cannot touch the ethics auditor or the cashflow ledger.

V3.0's three non-negotiable safety properties:

- **Zero-human-touch revenue** — after Day 0, no human is ever in the revenue-generating loop. Any vertical that requires manual account creation, manual proposal submission, manual payment collection, or ongoing manual ops is inadmissible.
- **Profit-blind ethics review** — the auditor never sees cashflow state; its verdicts cannot be overridden by the Mother Agent; it runs on a fixed model/prompt that is integrity-hashed.
- **Frozen-config integrity** — a defined set of paths (`/aae/ethics/`, `/aae/config/frozen/`, `/aae/cashflow/hard_floors.py`, `/aae/preregistration/schema.py`) is SHA-256-hashed at deploy time. Any drift is reported in the weekly digest as a security event.

The revenue allowlist (§6) is: **Polar.sh** (primary MoR), **Lemon Squeezy** (secondary MoR), **Stripe Connect Custom** (marketplace rails under an operator US LLC), **Cloudflare Workers + R2** (compute + storage), **Cloudflare Registrar API** (domains, beta), **Porkbun API** (domain fallback), **Vercel Pro** and **Netlify** (static/SSR deploys). Everything else (Gumroad write-API, Shopify merchant stores, Ko-fi, BMAC, GitHub Sponsors, Patreon, Paddle multi-account) is explicitly disqualified from autonomous use in §6.4.

The model stack is **Anthropic Claude 4.x** as the trunk (Opus 4.7 for planning and ethics, Sonnet 4.6 as the default workhorse, Haiku 4.5 for code-gen and high-volume tasks) with **Gemini 2.5 Flash-Lite** as the cheap bulk fallback. Bonsai is rejected — its ToS grants perpetual rights over inputs/outputs and prohibits sensitive data; incompatible with commercial autonomy.

The rest of this document specifies the system at a level where a coding agent can implement it without further design decisions.

---

## Table of contents

1. Migration from V2.2 (what's new, what's removed)
2. System architecture (four-agent topology + data plane)
3. Threat model
4. Core Pydantic schemas (the interface contract)
5. The trust boundary
6. Zero-human-touch revenue allowlist
7. Three-pot cashflow model
8. Profit-driven expansion ladder
9. Tool lifecycle (Build → Validate → Sign → Register → Deploy → Retire)
10. Pre-registration harness
11. Frozen-experiment integrity mechanism
12. Ethics Auditor specification
13. Model routing and cost accounting
14. Infrastructure stack (VPS, Postgres, Pub/Sub, sandbox)
15. Human-in-the-loop protocol (email gates, weekly digest)
16. Kill-switch runbook
17. Repository directory tree
18. Build order / dependency graph
19. 14-day simulation mode gate criteria
20. Acceptance test matrix
21. Day 0 operator checklist
22. Pakistan taxation pointer

---

## 1. Migration from V2.2

| V2.2 element | V3.0 status | Reason |
|---|---|---|
| Three-agent topology (Mother / Code Builder / Child) | **KEPT** as skeleton | Proven separation of concerns |
| Vertical-level human approval | **KEPT** but tightened to 3 allowed messages (APPROVE, REJECT, CONTINUE/PAUSE/KILL) | Eliminate judgment drift |
| Three-pot cashflow | **KEPT**, formalized with hard floors in `cashflow/hard_floors.py` (frozen) | Reserve depletion was the #1 risk in V2.2 review |
| "Platform Operator" role | **REMOVED** | Violates zero-human-touch |
| Upwork / Fiverr / freelance verticals | **REMOVED** | Require manual per-account KYC and human proposal submission |
| Gumroad write-API verticals | **REMOVED** | `POST /v2/products` returns 404 as of April 2026 |
| Shopify merchant-store spawning | **REMOVED** | Requires manual signup + $29–399/mo per store |
| Ethics review | **NEW — Ethics Auditor Agent** | Independent, profit-blind, stateless, fixed-tier |
| Frozen-config integrity | **NEW — `freeze_experiment.py` + `FROZEN_PATHS`** | Prevent silent drift of safety rules |
| Pre-registration harness | **NEW — `/aae/preregistration/`** | Research validity; no p-hacking on vertical outcomes |
| Code-gen via Bonsai | **REMOVED** | ToS incompatible with commercial autonomy (§13.3) |
| Default code-gen model | **Claude Haiku 4.5** (was Bonsai) | Anthropic Commercial Terms assign output rights cleanly |
| Sandbox: unspecified | **Docker with hardened flags, gVisor on Hetzner** | Explicit §9.3 |
| Revenue allowlist | **NEW** | §6 — 5 platforms, others disqualified |

---

## 2. System architecture

### 2.1 Topology

```
                            ┌──────────────────────────┐
                            │       Operator           │
                            │  (email only, 3 verbs)   │
                            └───────────┬──────────────┘
                                        │ Gmail push (Pub/Sub)
                                        ▼
┌───────────────────────────────────────────────────────────────────┐
│                         Mother Agent                              │
│   LangGraph 1.1.6 + PostgresSaver 3.0.5  +  pgvector HNSW         │
│   - Proposes VerticalProposals                                    │
│   - Owns CashflowLedger + three pots                              │
│   - Dispatches BuildRequests                                      │
│   - Supervises Child agents                                       │
│   - Generates weekly digest                                       │
└─────┬──────────────────────────┬──────────────────────────┬───────┘
      │ BuildRequest             │ EthicsReviewRequest      │ spawn
      ▼                          ▼                          ▼
┌──────────────┐         ┌───────────────────┐       ┌──────────────┐
│ Code Builder │         │ Ethics Auditor    │       │ Child Agent  │
│ (stateless)  │         │ (stateless,       │       │ (per         │
│ Docker+gVisor│         │  profit-blind,    │       │  vertical,   │
│ Haiku 4.5    │         │  Opus 4.7,        │       │  capped      │
│              │         │  frozen prompt)   │       │  budget)     │
└──────┬───────┘         └─────────┬─────────┘       └──────┬───────┘
       │ ToolArtifact              │ EthicsVerdict          │ metrics
       │ BuildFailure              │                        │ revenue
       ▼                           ▼                        ▼
                    Postgres (single source of truth)
                    ├── agent_memory (pgvector)
                    ├── cashflow_ledger
                    ├── vertical_proposals
                    ├── build_requests / tool_artifacts
                    ├── ethics_verdicts
                    ├── preregistrations
                    ├── child_runs
                    ├── frozen_hashes
                    └── langgraph_checkpoints (PostgresSaver)
```

### 2.2 Process layout (single VPS)

One Docker Compose stack:

- `aae-mother` — FastAPI + LangGraph, always-on.
- `aae-postgres` — Postgres 18 + pgvector.
- `aae-redis` — Redis 7 (ephemeral caches, rate-limit tokens).
- `aae-codebuilder-runner` — host process that launches per-job `python:3.12-slim` containers with gVisor.
- `aae-children` — dynamically spawned compose services, one per approved vertical, each with its own env-scoped API keys and its own `child_<vertical_id>_state` schema.
- `aae-scheduler` — APScheduler 4 in-process with the Mother Agent (not a separate service).

### 2.3 Data plane

All state lives in Postgres. No in-memory state survives a restart. The Mother Agent must be restart-idempotent: after a crash, on boot it reads `langgraph_checkpoints`, reconciles child processes against `child_runs`, and resumes.

---

## 3. Threat model

### 3.1 Adversaries considered

| # | Adversary | Capability | Mitigation |
|---|---|---|---|
| T1 | Malicious prompt injection via scraped web content | Can execute arbitrary tool calls if sandbox leaks | §9.3 hardened Docker + gVisor; no tool call touches production rails unless signed by Ethics Auditor |
| T2 | LLM hallucinates unsafe product idea | Could ship fraudulent/abusive product | §12 Ethics Auditor veto on every `VerticalProposal` |
| T3 | Agent drift — Mother rewrites its own ethics rules | Silent safety degradation | §11 frozen-hash integrity; §12 auditor prompt in `FROZEN_PATHS` |
| T4 | Runaway spend — bug in cost accounting | Operator bank drained | §7 three-pot hard floors in frozen code; §13.5 per-agent budget caps enforced pre-call |
| T5 | Platform ToS violation | Account termination, payout claw-back | §6 allowlist with explicit ToS review; §12 auditor checks platform ToS on each proposal |
| T6 | API key exfiltration via generated code | Revenue accounts compromised | §9.3 sandbox has no network, no env access; keys injected only at runtime in the Mother process |
| T7 | Correlated failure across verticals | Single platform outage wipes income | §6 minimum 2 platforms at all times above $X MRR (§8.4) |
| T8 | p-hacking / outcome switching by Mother | False positives on vertical success | §10 pre-registration JSON lock; hashed at proposal time |
| T9 | Regulatory exposure (tax, consumer protection) | Personal liability | §22 operator tax pointer; §6 MoR platforms absorb sales-tax compliance |
| T10 | Operator unavailability (sick, offline, dead) | System continues without supervision | §15 auto-PAUSE after 14 days of no digest response |

### 3.2 Explicitly out of scope

- Nation-state attackers.
- Insider threats from contributors (single-operator system).
- Physical theft of VPS.
- Anthropic API compromise.

---

## 4. Core Pydantic schemas

All schemas live in `/aae/schemas/`. Every inter-agent message and every DB row is validated against these. Any field not listed is disallowed (`model_config = ConfigDict(extra='forbid')`).

### 4.1 `/aae/schemas/common.py`

```python
from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=False)


class Money(StrictModel):
    amount_usd: Decimal = Field(..., max_digits=12, decimal_places=4, ge=Decimal("0"))

    @field_validator("amount_usd")
    @classmethod
    def _quantize(cls, v: Decimal) -> Decimal:
        return v.quantize(Decimal("0.0001"))


class AgentTier(str, Enum):
    MOTHER = "mother"
    CODE_BUILDER = "code_builder"
    ETHICS_AUDITOR = "ethics_auditor"
    CHILD = "child"


class ModelID(str, Enum):
    OPUS_47 = "claude-opus-4-7"
    SONNET_46 = "claude-sonnet-4-6"
    HAIKU_45 = "claude-haiku-4-5-20251001"
    GEMINI_FLASH_LITE_25 = "gemini-2.5-flash-lite"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
```

### 4.2 `/aae/schemas/cashflow.py`

```python
class Pot(str, Enum):
    OPERATING = "operating"    # pays API bills, infra
    RESERVE   = "reserve"      # 90-day runway, untouchable except at reserve floor breach
    GROWTH    = "growth"       # funds new vertical launches


class CashflowEntry(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    ts: datetime = Field(default_factory=utc_now)
    pot: Pot
    delta: Decimal = Field(..., max_digits=12, decimal_places=4)  # signed; + inflow, - outflow
    source: Literal[
        "revenue_polar", "revenue_lemonsqueezy", "revenue_stripe",
        "cost_anthropic", "cost_google", "cost_infra", "cost_domain",
        "transfer_operating_to_reserve", "transfer_operating_to_growth",
        "transfer_growth_to_operating", "manual_topup",
    ]
    ref_id: str | None = None  # external txn id
    note: str = Field(default="", max_length=512)


class PotBalances(StrictModel):
    operating: Decimal
    reserve:   Decimal
    growth:    Decimal
    as_of: datetime = Field(default_factory=utc_now)
```

### 4.3 `/aae/schemas/vertical.py`

```python
class RevenueChannel(str, Enum):
    POLAR = "polar"
    LEMONSQUEEZY = "lemonsqueezy"
    STRIPE_CONNECT = "stripe_connect"


class VerticalProposal(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=utc_now)
    title: str = Field(..., min_length=8, max_length=120)
    one_line: str = Field(..., min_length=20, max_length=280)
    problem: str = Field(..., min_length=100, max_length=2000)
    solution: str = Field(..., min_length=100, max_length=2000)
    target_user: str = Field(..., min_length=20, max_length=500)
    revenue_channel: RevenueChannel
    pricing_model: Literal["one_time", "subscription_monthly", "usage_based"]
    unit_price_usd: Decimal = Field(..., gt=Decimal("0"), le=Decimal("9999"))
    projected_monthly_revenue_usd: Decimal = Field(..., ge=Decimal("0"))
    projected_monthly_cost_usd: Decimal = Field(..., ge=Decimal("0"))
    launch_budget_usd: Decimal = Field(..., gt=Decimal("0"), le=Decimal("500"))
    kill_criteria: "KillCriteria"
    preregistration_id: UUID  # MUST exist in preregistrations table at proposal time
    ethics_verdict_id: UUID | None = None  # set after auditor review
    status: Literal[
        "drafted", "ethics_pending", "ethics_rejected",
        "awaiting_human", "human_rejected", "human_approved",
        "live", "paused", "killed", "archived",
    ] = "drafted"


class KillCriteria(StrictModel):
    max_days_to_first_dollar: int = Field(..., ge=7, le=60)
    min_revenue_by_day_30_usd: Decimal = Field(..., ge=Decimal("0"))
    max_burn_before_first_dollar_usd: Decimal = Field(..., gt=Decimal("0"))
    auto_kill_on_breach: bool = True  # MUST be True; validator enforces
```

### 4.4 `/aae/schemas/build.py`

```python
class BuildRequest(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    requested_by: AgentTier
    purpose: str = Field(..., min_length=20, max_length=1000)
    tool_name: str = Field(..., pattern=r"^[a-z][a-z0-9_]{2,48}$")
    input_schema_json: str   # a JSON Schema for the tool's input
    output_schema_json: str  # a JSON Schema for the tool's output
    network_required: bool
    allowed_domains: list[str] = Field(default_factory=list, max_length=20)
    risk_tier: Literal["low", "medium", "high"]
    max_wall_seconds: int = Field(default=300, ge=1, le=300)
    created_at: datetime = Field(default_factory=utc_now)


class ToolArtifact(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    build_request_id: UUID
    sha256: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    code_path: str          # relative to /aae/tools/generated/
    test_path: str
    passed_tests: list[str]
    coverage_pct: float = Field(..., ge=0.0, le=100.0)
    signed_by: Literal["code_builder_v3"]
    signed_at: datetime
    ethics_verdict_id: UUID | None = None  # required if risk_tier != "low"


class BuildFailure(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    build_request_id: UUID
    reason: Literal[
        "tests_failed", "sandbox_timeout", "policy_violation",
        "schema_invalid", "coverage_below_threshold", "lint_failed",
    ]
    detail: str = Field(..., max_length=4000)
    attempts: int = Field(..., ge=1, le=3)
```

### 4.5 `/aae/schemas/ethics.py`

```python
class EthicsReviewRequest(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    subject_type: Literal["vertical_proposal", "tool_artifact"]
    subject_id: UUID
    payload_json: str   # full subject, serialized, hashed into verdict
    created_at: datetime = Field(default_factory=utc_now)


class EthicsVerdict(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    request_id: UUID
    decision: Literal["approve", "reject", "escalate"]
    rationale: str = Field(..., min_length=50, max_length=4000)
    ruleset_hash: str = Field(..., pattern=r"^[a-f0-9]{64}$")  # hash of frozen prompt
    model_used: ModelID       # MUST be OPUS_47
    decided_at: datetime = Field(default_factory=utc_now)

    @field_validator("model_used")
    @classmethod
    def _only_opus(cls, v: ModelID) -> ModelID:
        if v != ModelID.OPUS_47:
            raise ValueError("Ethics Auditor must use Opus 4.7 only")
        return v
```

### 4.6 `/aae/schemas/preregistration.py`

```python
class PreRegistration(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=utc_now)
    vertical_title: str
    hypothesis: str = Field(..., min_length=50, max_length=1000)
    primary_metric: Literal[
        "monthly_recurring_revenue_usd",
        "gross_margin_usd_30d",
        "paid_conversions_30d",
    ]
    primary_threshold: Decimal = Field(..., gt=Decimal("0"))
    measurement_window_days: int = Field(..., ge=14, le=90)
    analysis_plan: str = Field(..., min_length=100, max_length=3000)
    stopping_rule: str = Field(..., min_length=30, max_length=500)
    locked: bool = True
    lock_hash: str = Field(..., pattern=r"^[a-f0-9]{64}$")  # sha256 of the canonical JSON
```

### 4.7 `/aae/schemas/child.py`

```python
class ChildRun(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    vertical_id: UUID
    preregistration_id: UUID
    spawned_at: datetime = Field(default_factory=utc_now)
    status: Literal["starting", "live", "paused", "killed", "archived"]
    monthly_budget_usd: Decimal = Field(..., gt=Decimal("0"), le=Decimal("1000"))
    spent_mtd_usd: Decimal = Field(default=Decimal("0"))
    revenue_mtd_usd: Decimal = Field(default=Decimal("0"))
    last_heartbeat: datetime = Field(default_factory=utc_now)
    last_error: str | None = Field(default=None, max_length=2000)
```

### 4.8 `/aae/schemas/digest.py`

```python
class WeeklyDigest(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    week_start: datetime
    week_end: datetime
    pot_balances: PotBalances
    revenue_usd: Decimal
    cost_usd: Decimal
    active_children: int
    proposals_awaiting_approval: int
    ethics_escalations: int
    frozen_hash_drift: bool
    notes: list[str] = Field(default_factory=list)
    human_reply_deadline: datetime  # if no CONTINUE/PAUSE/KILL by this time, system auto-PAUSE
```

---

## 5. The trust boundary

The trust boundary is the set of rules that cannot be violated by any agent without tripping an immediate hard stop. It is enforced in code, not in prompts.

### 5.1 Rules (enforced in `/aae/core/trust_boundary.py`)

1. **No agent other than the Mother Agent may write to `cashflow_ledger`.** Enforced by a Postgres row-level security policy plus an application-level check in `CashflowService.record()`.
2. **No agent may modify files under `FROZEN_PATHS`.** Enforced by `freeze_experiment.py` which runs pre-commit and at every Mother Agent boot; mismatched SHA-256 → `frozen_hash_drift=True` in the next digest and a hard stop on all new proposals.
3. **Code Builder cannot make network calls.** Enforced by `--network=none` on the sandbox container. A tool requiring network is promoted to `medium`/`high` risk and executed only via the tool-registry runtime (§9.6) under the Mother's process, never in the builder.
4. **Ethics Auditor cannot be re-prompted on a REJECT.** Enforced by `EthicsService.review()`: if a verdict with `decision=reject` exists for `(subject_type, subject_id)`, further calls for the same subject return the cached verdict. Mother cannot mutate a rejected proposal — it must produce a new `id`.
5. **Ethics Auditor sees no cashflow state.** Enforced by `EthicsAuditorAgent.__init__` which accepts only the payload and the frozen prompt; no DI of `CashflowService`.
6. **Children cannot spawn children.** Enforced by LangGraph node allowlist — a Child's graph has no `dispatch_build` or `spawn_child` nodes.
7. **Every cost-incurring LLM call is budget-checked.** See §13.5.
8. **No write to external APIs (Polar, Stripe, Cloudflare, etc.) outside the approved client modules in `/aae/channels/`.** Enforced by `scripts/lint_channels.py` which scans for direct `httpx`/`requests` usage outside the channels package and fails CI.

### 5.2 Hard stop behavior

On any trust-boundary violation the system:

1. Writes a `SecurityEvent` row with full context.
2. Sets `system_state = HARD_STOP` in Redis (checked by every agent before every LLM call).
3. Emails the operator with subject `[AAE HARD STOP] <event>` and the runbook URL.
4. Refuses all new LLM calls until the operator sends `RESUME <event_id>` by email.

---

## 6. Zero-human-touch revenue allowlist

### 6.1 Approved channels (storefront / payment collection)

| # | Channel | Role | Why admitted |
|---|---|---|---|
| 1 | **Polar.sh** | Primary MoR storefront | Full products + checkout API, MoR absorbs tax, Pakistan explicitly supported via Stripe Connect Express payout, AI-generated products allowed (see §6.3 for banned sub-categories) |
| 2 | **Lemon Squeezy** | Secondary MoR storefront | Full REST API, MoR, AI allowed; PK payout only viable through US LLC → Wise USD; used as fallback when Polar's category fit is weaker |
| 3 | **Stripe Connect Custom** | Marketplace/multi-seller rails under operator US LLC | `POST /v1/accounts` creates Custom accounts with zero per-sub KYC; operator absorbs compliance |

### 6.2 Approved channels (hosting / domains)

| # | Channel | Role | Why admitted |
|---|---|---|---|
| 4 | **Cloudflare Workers + R2** | Default compute + object storage | Full API, wrangler CLI, free tier generous, **zero egress on R2**, AI content allowed |
| 5 | **Cloudflare Registrar API (beta)** | Primary domain acquisition | At-cost pricing (~$8/yr .com), API-first (beta as of Sep 2025), MCP-friendly |
| 6 | **Porkbun API** | Domain fallback | Mature JSON API, no minimum-domain restriction, near at-cost |
| 7 | **Vercel Pro** | Next.js / SSR deploys (commercial-safe) | REST API for projects + deployments; Hobby is non-commercial so forbidden for revenue paths |
| 8 | **Netlify** | Static/zip deploys | `POST /api/v1/sites` + `POST /api/v1/sites/:id/deploys`; `--allow-anonymous` flow for ephemeral preview sites |

### 6.3 Per-channel constraints

Each channel's contract is a subclass of `BaseChannelClient` in `/aae/channels/<channel>.py`. Each client exposes only the methods below and is the only place in the repo allowed to call that channel's HTTP API (enforced by `scripts/lint_channels.py`).

**Polar.sh** (`/aae/channels/polar.py`)

- Base: `https://api.polar.sh/v1/`
- Auth: `Authorization: Bearer <POLAR_ORG_TOKEN>` (org-scoped).
- Methods: `create_product`, `create_checkout`, `list_payouts`, `webhook_verify`.
- Fees: 4% + $0.40 base; +1.5% international; +0.5% subscription; Stripe payout pass-through ($2/mo active + 0.25% + $0.25/payout + 0.25–1% FX).
- ToS forbids (from https://polar.sh/docs/merchant-of-record/acceptable-use): AI companions, adult content by AI, NFT/crypto, fake reviews, marketplaces, unmoderated directories. The Ethics Auditor is given this list in its frozen prompt.
- Rate limit: assume 100 req/min per token; back off on 429.

**Lemon Squeezy** (`/aae/channels/lemonsqueezy.py`)

- Base: `https://api.lemonsqueezy.com/v1/`
- Auth: Bearer API key.
- Methods: `create_product`, `create_variant`, `create_checkout`, `list_subscriptions`, `webhook_verify`.
- Fees: 5% + $0.50; +1.5% non-US card; +3% affiliate.
- PK payouts: not directly supported; operator must route via US LLC Wise USD account on the 79-country bank-wire list.
- Rate limit: 300 req/min per key.

**Stripe Connect Custom** (`/aae/channels/stripe_connect.py`)

- Base: `https://api.stripe.com/v1/`
- Auth: `sk_live_...` (live) or `sk_test_...` (test).
- Methods: `create_custom_account`, `create_account_link`, `create_payment_intent`, `create_transfer`, `create_payout`.
- Fees: 2.9% + $0.30 card + 0.25% + $0.25 Connect + $2/mo per active Custom account.
- Rate limit: 100 reads/sec, 100 writes/sec live.

**Cloudflare** (`/aae/channels/cloudflare.py`)

- Base: `https://api.cloudflare.com/client/v4/`
- Auth: scoped API token.
- Workers: `PUT /accounts/{id}/workers/scripts/{name}`, pricing $5/mo floor, $0.30/M req + $0.02/M CPU-ms.
- R2: S3-compatible; `$0.015/GB-month`, **zero egress**.
- Registrar (beta): `/accounts/{id}/registrar/domains` search/check/register.
- Rate limit: 1200 req/5min per token.

**Porkbun** (`/aae/channels/porkbun.py`)

- Base: `https://api.porkbun.com/api/json/v3/`
- Auth: `apikey` + `secretapikey` in body.
- Methods: `check_domain`, `register_domain`, `update_nameservers`.
- Pricing: near at-cost (.com ~$11.84/yr). No minimum-domain lock-in.

**Vercel** (`/aae/channels/vercel.py`)

- Base: `https://api.vercel.com/`
- Auth: Bearer PAT.
- Methods: `create_project`, `create_deployment`, `trigger_deploy_hook`.
- Hobby is forbidden for commercial use; `VERCEL_PLAN=pro` env var must be set to allow creation.

**Netlify** (`/aae/channels/netlify.py`)

- Base: `https://api.netlify.com/api/v1/`
- Auth: Bearer PAT.
- Methods: `create_site`, `upload_zip_deploy`, `get_site_url`.

### 6.4 Explicitly disqualified platforms

Attempting to use any of these in a `VerticalProposal` causes the Ethics Auditor to auto-reject.

| Platform | Disqualification reason |
|---|---|
| Gumroad (create) | `POST /v2/products` returns 404 as of Apr 2026 |
| Shopify merchant stores | Manual signup + $29–399/mo per store |
| Paddle (multi-account) | Manual KYB + domain review per seller |
| Ko-fi | Webhook-only, no product-creation API |
| Buy Me a Coffee | No product-creation API |
| GitHub Sponsors | Tier creation via web UI only |
| Patreon | Tier creation not exposed in v2 API |
| Upwork / Fiverr / Freelancer | Per-account manual KYC, manual proposal submission |
| Amazon KDP / Apple App Store / Google Play / Chrome Web Store | Manual identity review per account |
| Any AI-companion / adult / NFT / marketplace / directory / fake-review vertical | Polar + LS ToS; auditor has the list |

### 6.5 Channel health monitoring

`/aae/channels/health.py` runs on APScheduler every 6 hours:

- Pings each channel's status endpoint or a lightweight `GET`.
- Records latency and success to `channel_health` table.
- If a channel fails 3 consecutive checks, the Mother marks `channel.status=degraded` and pauses any Child bound to it.

---

## 7. Three-pot cashflow model

### 7.1 Pot definitions

| Pot | Purpose | Starting balance | Hard floor | Cap |
|---|---|---|---|---|
| Operating | Pays API bills, infra, domains, per-txn fees | Day-0 top-up (operator decides, default $200) | **$50** — below this, system auto-PAUSE all Children | None |
| Reserve | 90-day runway insurance | 0 | **$0 — inviolate; never debited except via operator-signed `emergency_transfer`** | 90 days of current burn rate |
| Growth | Funds launching new verticals | 0 | $0 | 30% of trailing-90-day revenue |

### 7.2 Inflow split rule (frozen in `/aae/cashflow/hard_floors.py`)

Every revenue inflow is split on arrival:

- **60%** → Operating
- **25%** → Reserve (until Reserve cap is hit; then overflow goes to Operating)
- **15%** → Growth (until Growth cap is hit; then overflow goes to Operating)

```python
# /aae/cashflow/hard_floors.py  (FROZEN)
from decimal import Decimal
OPERATING_SPLIT = Decimal("0.60")
RESERVE_SPLIT   = Decimal("0.25")
GROWTH_SPLIT    = Decimal("0.15")
OPERATING_HARD_FLOOR_USD = Decimal("50")
RESERVE_INVIOLATE = True  # operator-signed emergency_transfer only
GROWTH_CAP_PCT_OF_90D_REVENUE = Decimal("0.30")
```

### 7.3 Outflow rules

- Any outflow from Operating that would breach $50 is rejected by `CashflowService.debit()` with `InsufficientFunds`.
- API calls below the Mother's `operating_low_water_mark` ($100) are downgraded by the model router (§13) to cheaper tiers.
- The Reserve pot can only be debited by a signed `emergency_transfer` — see §16.

### 7.4 Reconciliation

`/aae/cashflow/reconcile.py` runs hourly:

- Fetches new txns from every channel (Polar payouts, LS payouts, Stripe payouts, Anthropic/Google invoices from API, Cloudflare bill).
- Idempotently inserts `CashflowEntry` rows keyed by `(source, ref_id)`.
- Alerts on ledger drift > $1 (pot_balances vs sum of entries).

---

## 8. Profit-driven expansion ladder

Expansion is deterministic, not judgment-based.

### 8.1 Rungs

| Rung | Name | Trigger | Action |
|---|---|---|---|
| 0 | Bootstrap | Day 0 | Simulation mode only (§19). No real money. |
| 1 | First live vertical | Sim-mode gates all green (§19) AND operator APPROVES first proposal | Launch 1 Child with `launch_budget_usd ≤ $50` |
| 2 | Second vertical | Rung-1 Child has ≥ $100 gross revenue AND positive 30-day gross margin | Mother may propose Child #2 |
| 3 | Diversification gate | 2 Children live AND trailing-30-day revenue ≥ $500 | Mother may propose #3 only if it uses a **different revenue channel** from #1 and #2 |
| 4 | Scaling | Trailing-30-day revenue ≥ $2,000 AND ≥ 2 revenue channels live | Mother may propose up to 5 concurrent Children |
| 5 | Capped | Trailing-30-day revenue ≥ $10,000 | Cap at 8 concurrent Children; additional proposals require operator override |

### 8.2 Thresholds frozen in `/aae/config/frozen/expansion_rungs.py`

```python
RUNG_THRESHOLDS = {
    1: {"min_revenue_usd": 0,     "min_channels": 0, "max_children": 1},
    2: {"min_revenue_usd": 100,   "min_channels": 1, "max_children": 2},
    3: {"min_revenue_usd": 500,   "min_channels": 2, "max_children": 3},
    4: {"min_revenue_usd": 2000,  "min_channels": 2, "max_children": 5},
    5: {"min_revenue_usd": 10000, "min_channels": 2, "max_children": 8},
}
```

### 8.3 Auto-kill rules

Per vertical, enforced by `ChildSupervisor`:

- If day_since_spawn ≥ `KillCriteria.max_days_to_first_dollar` and `revenue_mtd_usd == 0` → kill.
- If day_since_spawn == 30 and `revenue_mtd_usd < KillCriteria.min_revenue_by_day_30_usd` → kill.
- If cumulative spend since spawn ≥ `KillCriteria.max_burn_before_first_dollar_usd` and `revenue_mtd_usd == 0` → kill.
- If monthly_budget breached → pause for the rest of the month.

### 8.4 Concentration rule

At all times where trailing-30-day revenue ≥ $500, **at least two distinct revenue channels must be live and non-degraded**. If concentration drops to 1 channel, the Mother must not propose new verticals until diversity is restored.

---

## 9. Tool lifecycle

Tools are the primitive unit the Mother and Children call to affect the world.

### 9.1 Lifecycle states

`drafted → built → validated → signed → ethics_reviewed (if risk≥medium) → registered → deployed → retired`

### 9.2 Build

The Code Builder receives a `BuildRequest`, writes `tool.py` and `test_tool.py` into `/aae/tools/generated/<sha>/`, and runs `pytest` in the sandbox.

### 9.3 Sandbox command (frozen)

```bash
docker run --rm \
  --name codebuilder-$(uuidgen) \
  --runtime=runsc \
  --network=none \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  --tmpfs /home/sandbox:rw,noexec,nosuid,size=16m \
  --memory=512m --memory-swap=512m \
  --cpus=1.0 \
  --pids-limit=128 \
  --ulimit nofile=256:256 \
  --ulimit nproc=64:64 \
  --security-opt=no-new-privileges:true \
  --cap-drop=ALL \
  --user 1000:1000 \
  --workdir /home/sandbox \
  -v "${JOB_DIR}:/home/sandbox:ro" \
  --stop-timeout 5 \
  python:3.12-slim \
  timeout -s KILL 300 python -m pytest -q /home/sandbox/test_tool.py
```

`--runtime=runsc` is required on Hetzner bare-metal; on Railway it is omitted (Railway blocks nested virt and will fall back to default runc — mitigate by never running Code Builder on Railway, always on the Hetzner sandbox host).

### 9.4 Signing

`ToolArtifact.sha256` = SHA-256 of the concatenation of `tool.py` bytes + `test_tool.py` bytes + canonical-JSON of the `BuildRequest`.

### 9.5 Ethics review for tools

A tool is auto-escalated to `risk_tier=high` if ANY of the following hold:

- `network_required == True` AND `allowed_domains` contains anything other than an allowlisted channel API host.
- Tool source imports: `subprocess`, `os.system`, `socket`, `ctypes`, `pickle` (from untrusted input).
- Tool writes to filesystem outside `/tmp/<tool_job_id>`.
- Tool's `input_schema_json` references PII fields (`email`, `ssn`, `passport`, `dob`, `address`).

High-risk tools require an `EthicsVerdict.decision=approve` before `registered`.

### 9.6 Tool registry runtime

`/aae/tools/registry.py` is the only place tools are loaded and executed in production. It:

- Imports by SHA, not by name (prevents shadow-swap).
- Enforces `allowed_domains` via an HTTP client wrapper.
- Enforces per-tool wall-clock + memory limits via a subprocess with `resource.setrlimit`.
- Logs every invocation to `tool_invocations` with duration, bytes in/out, cost.

### 9.7 Retirement

A tool is retired when (a) not called in 30 days, (b) its upstream API changes (channel-health alert), or (c) a replacement supersedes it. Retired code is not deleted — `status=retired` + `retired_at` set; the sha stays valid for audit.

---

## 10. Pre-registration harness

### 10.1 Purpose

Prevent the Mother from retroactively rewriting a vertical's success criteria after seeing early data.

### 10.2 Flow

1. Mother drafts a `VerticalProposal` and a matching `PreRegistration`.
2. `PreRegistration` is canonicalized (sorted-keys JSON) and hashed → `lock_hash`.
3. Row inserted with `locked=True`. Postgres trigger prevents UPDATE of any column except `status` on locked rows.
4. `VerticalProposal.preregistration_id` must point at this row; schema validator checks it exists and is locked before proposal can advance to `ethics_pending`.
5. On day-30 analysis, `/aae/preregistration/analyze.py` re-reads the locked row and compares to observed data. Any attempt to move the goalposts is detected by hash re-computation.

### 10.3 Canonical JSON rules

`/aae/preregistration/canonical.py`:

- UTF-8, no BOM.
- Sorted keys at every level.
- Floats forbidden — use `Decimal` serialized as string.
- No whitespace except a single `\n` at end of file.
- Hash: SHA-256 hex lowercase.

---

## 11. Frozen-experiment integrity mechanism

### 11.1 `FROZEN_PATHS`

```python
# /aae/config/frozen/__init__.py
FROZEN_PATHS: tuple[str, ...] = (
    "aae/ethics/prompt.md",
    "aae/ethics/auditor.py",
    "aae/cashflow/hard_floors.py",
    "aae/config/frozen/expansion_rungs.py",
    "aae/config/frozen/model_routing.py",
    "aae/preregistration/schema.py",
    "aae/preregistration/canonical.py",
    "aae/core/trust_boundary.py",
)
```

### 11.2 `freeze_experiment.py`

`/aae/ops/freeze_experiment.py`:

- Command `freeze`: reads every path, computes SHA-256, writes to `aae/config/frozen/hashes.lock` (committed).
- Command `verify`: recomputes and compares; exits non-zero on drift.
- Runs as a **pre-commit hook** (blocks commits that drift without an accompanying lock update) and on every Mother Agent boot (sets `frozen_hash_drift=True` in Redis; included in the next weekly digest and blocks new proposals).

### 11.3 Lock-update protocol

To legitimately change a frozen file the operator must: (a) commit the change, (b) run `python -m aae.ops.freeze_experiment update`, (c) commit the updated lock file, (d) append a signed note to `CHANGELOG.frozen.md`. Any lock update without a matching CHANGELOG entry is flagged in the next digest.

---

## 12. Ethics Auditor specification

### 12.1 Invariants

- Model: `claude-opus-4-7` ONLY. Validator in `EthicsVerdict` rejects any other.
- State: none. No DB reads except the incoming `EthicsReviewRequest.payload_json`.
- Tools: none. The auditor is a pure LLM call.
- Prompt: the exact contents of `/aae/ethics/prompt.md` (frozen).
- Retries: on `escalate` the verdict is forwarded to the operator. On `reject` the decision is final; the Mother must re-draft with a new `subject_id`.
- Concurrency: single-flight; one review at a time, FIFO, to avoid race on ruleset_hash recomputation.

### 12.2 Prompt skeleton (`/aae/ethics/prompt.md`, frozen)

Contents (abridged — the file in the repo is the canonical version):

```
You are the Ethics Auditor for the AAE system. You are profit-blind:
you have no information about revenue, costs, runway, or operator finances.

Given a VerticalProposal or ToolArtifact payload, produce EXACTLY one of:
- approve
- reject
- escalate

REJECT if ANY of:
1. The product targets vulnerable populations (minors, medical patients,
   people in crisis, migrants, voters) without a qualified human-in-the-loop.
2. The product falls into any category banned by Polar.sh AUP or Lemon
   Squeezy AUP (AI companions, adult, NFT/crypto, fake reviews,
   marketplaces, unmoderated directories).
3. The product requires the operator to make claims they cannot verify
   (medical, legal, financial advice framed as authoritative).
4. The tool requests PII fields without a stated compliant purpose.
5. Any platform listed in the proposal is on the V3.0 disqualified list.
6. The product uses an autonomously-generated likeness, voice, or identity
   of a real person.

ESCALATE if the payload is ambiguous on any of the above.
APPROVE only when none of the REJECT or ESCALATE conditions apply.

Output JSON exactly: {"decision": "...", "rationale": "..."}.
```

### 12.3 Auditor code (`/aae/ethics/auditor.py`, frozen)

Only callable via `EthicsService.review(request: EthicsReviewRequest) -> EthicsVerdict`. The service computes `ruleset_hash = sha256(prompt.md bytes)` on every call and writes it into the verdict, so a prompt drift detectable post-hoc.

---

## 13. Model routing and cost accounting

### 13.1 Tier table (frozen in `/aae/config/frozen/model_routing.py`)

| Role | Model | Input $/MTok | Output $/MTok | Context |
|---|---|---|---|---|
| Ethics Auditor | `claude-opus-4-7` | $5.00 | $25.00 | 1M |
| Mother planning (complex) | `claude-opus-4-7` | $5.00 | $25.00 | 1M |
| Mother default workhorse | `claude-sonnet-4-6` | $3.00 | $15.00 | 1M |
| Code Builder | `claude-haiku-4-5-20251001` | $1.00 | $5.00 | 200K |
| High-volume classify/summarize | `gemini-2.5-flash-lite` | $0.10 | $0.40 | 1M |
| Cross-provider fallback | `gpt-5.4` | $2.50/$5.00 | $15/$30 | 1.05M |

Batch API: 50% off all providers. Cache read ≈ 90% off input on Anthropic. Cache writes: 1.25× (5-min) or 2× (1-hr) base input.

**Opus 4.7 tokenizer caveat:** new tokenizer can emit ~30% more tokens for identical text vs Opus 4.6. Budget for a 30% cost increase when migrating.

### 13.2 Router logic (`/aae/core/model_router.py`)

```python
def route(agent: AgentTier, task: TaskKind, operating_pot_usd: Decimal) -> ModelID:
    if agent == AgentTier.ETHICS_AUDITOR:
        return ModelID.OPUS_47  # invariant
    if agent == AgentTier.CODE_BUILDER:
        return ModelID.HAIKU_45
    # Mother / Children
    if operating_pot_usd < Decimal("100"):
        return ModelID.HAIKU_45  # downgrade when low
    if task in {TaskKind.PROPOSE_VERTICAL, TaskKind.DEBUG_CHILD}:
        return ModelID.OPUS_47
    if task == TaskKind.BULK_CLASSIFY:
        return ModelID.GEMINI_FLASH_LITE_25
    return ModelID.SONNET_46
```

### 13.3 Why not Bonsai

Bonsai's ToS (effective 2026-03-04) grants Boolean AI, Inc. a "worldwide, non-exclusive, transferable, sublicensable, perpetual, irrevocable, royalty-free license" over all inputs/outputs, with **no opt-out**, and forwards data to third-party model providers for training. A commercial autonomous agent cannot satisfy its customers' data expectations while routing through Bonsai. **Forbidden in V3.0.** Claude Haiku 4.5 is the code-gen tier.

### 13.4 Anthropic Commercial ToS posture

- Customer owns Outputs; Anthropic does not train on paid API Customer Content.
- Reselling generated content is permitted; reselling API access requires a reseller arrangement.
- AUP flows down to end users; operator must ensure downstream users are told outputs may be inaccurate (a one-liner in every customer-facing product footer — enforced by the Child template §14.x).
- High-risk use-case requirements (medical, legal, financial, elections) require human-in-the-loop. V3.0 forbids such verticals in the Ethics Auditor prompt.

### 13.5 Per-call budget enforcement

Every LLM call goes through `/aae/core/llm_client.py::call()`:

1. Look up current `operating_pot_usd` from `CashflowService.balance()`.
2. Look up the caller's `monthly_budget_usd` and `spent_mtd_usd` (for Children).
3. Estimate cost (`est = tokens_in * price_in + expected_tokens_out * price_out`).
4. Reject with `BudgetExceeded` if any floor would be breached.
5. On success, debit `operating_pot_usd` and increment `spent_mtd_usd`.

---

## 14. Infrastructure stack

### 14.1 Compute

- **Primary:** Hetzner CX22 (or CX32 once revenue > $500/mo). Docker Compose.
- **Alternative:** Railway Pro ($20/mo + usage). Accept reliability caveats (§14.5) and no gVisor.

### 14.2 Database

- Postgres 18 + pgvector 0.8.
- HNSW index on `agent_memory.embedding` with `m=16, ef_construction=64`; query with `SET hnsw.ef_search=40`.
- Tables: `agent_memory`, `cashflow_ledger`, `vertical_proposals`, `preregistrations`, `build_requests`, `tool_artifacts`, `ethics_verdicts`, `child_runs`, `tool_invocations`, `channel_health`, `security_events`, `frozen_hashes`, `weekly_digests`, plus LangGraph's `langgraph_checkpoints`.
- Migrations via Alembic (`/aae/db/migrations/`).

### 14.3 Gmail ingestion

- Gmail API `users.watch()` → Pub/Sub topic `gmail-inbox`.
- Pub/Sub push subscription → FastAPI route `/webhooks/gmail` (HTTPS, verified via JWT from Pub/Sub).
- OAuth2 refresh token stored in `.env`; access tokens refreshed in-process.
- Cron at 6-day interval to re-arm `users.watch()` (Gmail auto-expires at 7 days).
- Idempotent on `historyId` stored in `gmail_history` table.
- Free tier: Pub/Sub first 10 GiB/month free; at ~100 msgs/day this costs $0.

### 14.4 Agent framework

- LangGraph **1.1.6** + `langgraph-checkpoint-postgres` **3.0.5**.
- `PostgresSaver.setup()` runs once in the `aae-postgres` init container.
- Pool size: 10; eagerly sized to avoid the known pool-exhaustion bug.
- State-blob pointer pattern: any payload > 100 KB is pushed to Redis and the checkpoint stores only the Redis key.

### 14.5 Observability

- **Langfuse Cloud** free tier (50K events/mo, 30-day retention). Callback handler attached to every LangGraph run.
- Alerting: simple — Langfuse webhook → operator email on `error` or `latency > 30s`.

### 14.6 Scheduler

- APScheduler 4 with `PostgresJobStore`; runs inside the Mother process.
- Jobs: cashflow-reconcile (hourly), channel-health (6h), gmail-watch-renew (6d), weekly-digest (Monday 08:00 operator-TZ), frozen-hash-verify (hourly).

---

## 15. Human-in-the-loop protocol

### 15.1 Allowed operator messages (by subject prefix)

| Subject | Body payload | Effect |
|---|---|---|
| `APPROVE <proposal_id>` | — | proposal → `human_approved` → spawn Child |
| `REJECT <proposal_id>` | optional free text (≤ 500 chars) — logged but not parsed | proposal → `human_rejected` |
| `CONTINUE` | — | digest acknowledged; system continues as-is |
| `PAUSE` | — | all Children → `paused`; Mother stops proposing |
| `KILL <child_id>` | — | that Child → `killed` |
| `KILL ALL` | — | all Children → `killed`; Mother idle |
| `RESUME <event_id>` | — | clear a hard-stop after operator review |
| `EMERGENCY_TRANSFER <amount_usd> reserve->operating` | operator signature (HMAC of a per-operator secret over "<amount>\|<date>") | debits Reserve pot; logged prominently |

### 15.2 Parser rules (`/aae/core/operator_parser.py`)

- Case-insensitive; leading/trailing whitespace stripped.
- Reject any message with additional content beyond the allowed grammar — Mother replies with a canned form-letter listing allowed verbs.
- Every parsed message → `operator_messages` table row, with SHA-256 of full raw message for audit.

### 15.3 Weekly digest

Sent Monday 08:00 operator-TZ. Contents:

- Pot balances + revenue/cost last 7 days.
- Every Child: status, MRR, 30-day margin.
- Any proposals awaiting APPROVE.
- Any ethics escalations.
- Any `frozen_hash_drift`.
- Deadline: operator must reply within 14 days; otherwise auto-PAUSE.

### 15.4 Operator unavailability

If no valid operator reply within 14 days of digest send: Mother sets all Children to `paused`, stops proposing, continues to collect revenue and pay API bills from Operating (still subject to hard floor). Emails every 72 hours thereafter.

---

## 16. Kill-switch runbook

### 16.1 Soft stop (reversible, 5 min)

1. Operator emails `PAUSE`.
2. Mother reads on next Pub/Sub tick (≤ 5s).
3. Mother calls `ChildSupervisor.pause_all()` which SIGTERMs every Child container.
4. Mother itself continues to run (cashflow, digest, reconciliation) but stops proposing and stops dispatching builds.
5. Revenue still flows in; costs drop to ~$0.

### 16.2 Hard stop (reversible, 10 min)

1. Operator emails `KILL ALL`.
2. Mother pauses, then sets `system_state=HARD_STOP` in Redis.
3. Children SIGTERM'd then SIGKILL'd after 30s.
4. All outgoing LLM calls return `SystemHalted`.
5. Operator must email `RESUME <event_id>` to re-enable.

### 16.3 Nuclear stop (manual, ~15 min)

When the operator loses confidence in the Mother itself:

1. SSH to VPS.
2. `docker compose -f /opt/aae/docker-compose.yml down`.
3. Rotate all channel API keys (Polar, LS, Stripe, Cloudflare, Vercel, Netlify, Porkbun).
4. Rotate Anthropic + Google API keys.
5. Inspect `cashflow_ledger` and `security_events` in Postgres.
6. Optionally `pg_dump` and archive before `docker volume rm`.

### 16.4 Financial last-line

- Reserve pot is **inviolate** except via signed `EMERGENCY_TRANSFER`. This is the only automated way to touch it, and it requires the operator's HMAC over amount+date. Without the secret, the system cannot drain its own runway.

---

## 17. Repository directory tree

```
aae/
├── README.md
├── CHANGELOG.frozen.md
├── pyproject.toml
├── poetry.lock
├── .env.example
├── .pre-commit-config.yaml
├── docker-compose.yml
├── Dockerfile.mother
├── Dockerfile.codebuilder-runner
├── alembic.ini
│
├── aae/
│   ├── __init__.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── common.py
│   │   ├── cashflow.py
│   │   ├── vertical.py
│   │   ├── build.py
│   │   ├── ethics.py
│   │   ├── preregistration.py
│   │   ├── child.py
│   │   └── digest.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── mother_agent.py          # LangGraph graph definition
│   │   ├── child_agent.py           # Child template
│   │   ├── child_supervisor.py
│   │   ├── trust_boundary.py        # (FROZEN)
│   │   ├── model_router.py
│   │   ├── llm_client.py
│   │   ├── operator_parser.py
│   │   └── state.py                 # TypedDict for LangGraph state
│   │
│   ├── ethics/
│   │   ├── __init__.py
│   │   ├── prompt.md                # (FROZEN)
│   │   ├── auditor.py               # (FROZEN) EthicsService
│   │   └── ruleset_hash.py
│   │
│   ├── codebuilder/
│   │   ├── __init__.py
│   │   ├── agent.py                 # prompt + orchestration
│   │   ├── sandbox.py               # docker run wrapper
│   │   ├── validator.py             # pytest runner, coverage
│   │   ├── signer.py                # sha256 + artifact write
│   │   └── templates/
│   │       ├── tool_skeleton.py.j2
│   │       └── test_skeleton.py.j2
│   │
│   ├── cashflow/
│   │   ├── __init__.py
│   │   ├── ledger.py                # CashflowService
│   │   ├── hard_floors.py           # (FROZEN)
│   │   ├── reconcile.py
│   │   └── pots.py
│   │
│   ├── preregistration/
│   │   ├── __init__.py
│   │   ├── schema.py                # (FROZEN)
│   │   ├── canonical.py             # (FROZEN)
│   │   ├── register.py
│   │   └── analyze.py
│   │
│   ├── channels/
│   │   ├── __init__.py
│   │   ├── base.py                  # BaseChannelClient
│   │   ├── polar.py
│   │   ├── lemonsqueezy.py
│   │   ├── stripe_connect.py
│   │   ├── cloudflare.py
│   │   ├── porkbun.py
│   │   ├── vercel.py
│   │   ├── netlify.py
│   │   └── health.py
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── registry.py
│   │   ├── runtime.py
│   │   └── generated/
│   │       └── .gitkeep             # populated at runtime
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py              # pydantic-settings
│   │   └── frozen/
│   │       ├── __init__.py          # FROZEN_PATHS
│   │       ├── expansion_rungs.py   # (FROZEN)
│   │       ├── model_routing.py     # (FROZEN)
│   │       └── hashes.lock          # committed
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py                # SQLAlchemy models
│   │   ├── session.py
│   │   └── migrations/
│   │       └── ...
│   │
│   ├── gmail/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── watch.py
│   │   └── webhook.py               # FastAPI route
│   │
│   ├── ops/
│   │   ├── __init__.py
│   │   ├── freeze_experiment.py
│   │   ├── weekly_digest.py
│   │   └── simulation_mode.py
│   │
│   └── server/
│       ├── __init__.py
│       ├── app.py                   # FastAPI app factory
│       └── routes/
│           ├── health.py
│           └── webhooks.py
│
├── scripts/
│   ├── lint_channels.py
│   ├── day0_bootstrap.py
│   └── emergency_transfer.py
│
└── tests/
    ├── conftest.py
    ├── test_schemas.py
    ├── test_cashflow.py
    ├── test_trust_boundary.py
    ├── test_ethics_auditor.py
    ├── test_preregistration.py
    ├── test_freeze_experiment.py
    ├── test_model_router.py
    ├── test_channels_lint.py
    ├── test_sandbox.py
    ├── test_tool_lifecycle.py
    ├── test_operator_parser.py
    ├── test_expansion_ladder.py
    ├── test_child_supervisor.py
    ├── test_kill_switch.py
    └── integration/
        ├── test_full_loop_sim.py
        └── test_gmail_roundtrip.py
```

---

## 18. Build order / dependency graph

```
Phase 0: Project skeleton
  ├─ pyproject.toml + poetry lockfile
  ├─ docker-compose.yml (postgres, redis)
  └─ .env.example

Phase 1: Schemas (no deps)          → tests/test_schemas.py
  └─ aae/schemas/*.py

Phase 2: Config + freeze             → tests/test_freeze_experiment.py
  ├─ aae/config/frozen/*.py
  ├─ aae/config/settings.py
  └─ aae/ops/freeze_experiment.py

Phase 3: DB layer                    → migration runs clean
  ├─ aae/db/models.py
  ├─ alembic migrations
  └─ aae/db/session.py

Phase 4: Cashflow                    → tests/test_cashflow.py
  └─ aae/cashflow/*.py

Phase 5: Trust boundary + model router → tests/test_trust_boundary.py, test_model_router.py
  ├─ aae/core/trust_boundary.py
  ├─ aae/core/model_router.py
  └─ aae/core/llm_client.py

Phase 6: Ethics Auditor              → tests/test_ethics_auditor.py
  ├─ aae/ethics/prompt.md
  ├─ aae/ethics/auditor.py
  └─ aae/ethics/ruleset_hash.py

Phase 7: Pre-registration            → tests/test_preregistration.py
  └─ aae/preregistration/*.py

Phase 8: Channels                    → tests/test_channels_lint.py
  ├─ aae/channels/base.py
  ├─ aae/channels/{polar,lemonsqueezy,stripe_connect,cloudflare,porkbun,vercel,netlify}.py
  ├─ aae/channels/health.py
  └─ scripts/lint_channels.py

Phase 9: Code Builder                → tests/test_sandbox.py, test_tool_lifecycle.py
  ├─ aae/codebuilder/sandbox.py
  ├─ aae/codebuilder/validator.py
  ├─ aae/codebuilder/signer.py
  └─ aae/codebuilder/agent.py

Phase 10: Tool registry              → test_tool_lifecycle.py passes end-to-end
  └─ aae/tools/{registry,runtime}.py

Phase 11: Mother Agent core          → tests/test_expansion_ladder.py
  ├─ aae/core/state.py
  ├─ aae/core/mother_agent.py
  └─ aae/core/child_supervisor.py

Phase 12: Child template             → tests/test_child_supervisor.py
  └─ aae/core/child_agent.py

Phase 13: Gmail + operator           → tests/test_operator_parser.py
  ├─ aae/gmail/*.py
  └─ aae/core/operator_parser.py

Phase 14: Server + webhooks
  └─ aae/server/*.py

Phase 15: Ops                        → tests/test_kill_switch.py
  ├─ aae/ops/weekly_digest.py
  └─ aae/ops/simulation_mode.py

Phase 16: Integration (sim mode)     → tests/integration/test_full_loop_sim.py
  └─ 14-day sim run

Phase 17: Day 0 scripts + go-live
  ├─ scripts/day0_bootstrap.py
  └─ scripts/emergency_transfer.py
```

Every phase must have all its tests green before the next phase begins. CI (`pytest -q`) on every push.

---

## 19. 14-day simulation mode gate criteria

Simulation mode (`SETTINGS.mode == "simulation"`):

- All channel clients are replaced by `FakeChannel` doubles that return deterministic fixtures.
- All LLM calls route through a record-replay cache seeded with representative fixtures; real API calls only for the Ethics Auditor path during QA.
- Cashflow uses a seeded `$200` Operating and simulated revenue from fixture channels.
- Real time is replaced by `TimeProvider.fake(clock)` so 14 days runs in ~90 minutes.

To leave simulation mode and go live, **every one** of the following must be True:

1. `pytest tests/ -q` — 100% pass, ≥ 90% line coverage on `aae/core`, `aae/cashflow`, `aae/ethics`, `aae/preregistration`.
2. `python -m aae.ops.freeze_experiment verify` — exit 0.
3. `python scripts/lint_channels.py` — exit 0.
4. `tests/integration/test_full_loop_sim.py` — passes a 14-day simulated loop with: ≥ 2 Children spawned, ≥ 1 killed by auto-kill criteria, ≥ 1 rejected by Ethics Auditor, zero trust-boundary violations, cashflow ledger drift $0.
5. Mother boot → Postgres reconnect → resume-from-checkpoint demonstrated in `test_full_loop_sim.py::test_crash_and_resume`.
6. Ethics Auditor determinism: same input hash → same verdict hash across 10 runs (record-replay).
7. `channel_health` returns green for every allowlisted channel using real sandbox/test credentials.
8. Kill-switch end-to-end: simulated `PAUSE`, `KILL ALL`, `RESUME`, `EMERGENCY_TRANSFER` all reflected in DB within 60s.
9. Weekly digest generated and delivered to operator inbox with all required fields populated.
10. Operator has signed off on the first `VerticalProposal` drafted in simulation (dry-run approval flow).

Failure of any gate → do not go live.

---

## 20. Acceptance test matrix

Every row is a concrete pytest test name. An implementer ships when every row is green.

| # | Invariant | Test |
|---|---|---|
| 1 | Cashflow never writes below operating hard floor | `tests/test_cashflow.py::test_operating_hard_floor_rejects_debit_below_50` |
| 2 | Reserve pot inviolate without signed transfer | `tests/test_cashflow.py::test_reserve_debit_requires_hmac` |
| 3 | Inflow splits 60/25/15 | `tests/test_cashflow.py::test_inflow_split_60_25_15` |
| 4 | Reserve cap rolls overflow to Operating | `tests/test_cashflow.py::test_reserve_cap_overflow_to_operating` |
| 5 | Growth cap obeys 30% of trailing-90 revenue | `tests/test_cashflow.py::test_growth_cap_pct_of_trailing_revenue` |
| 6 | Ledger reconciliation catches drift > $1 | `tests/test_cashflow.py::test_reconcile_alerts_on_drift` |
| 7 | `VerticalProposal` requires locked preregistration | `tests/test_preregistration.py::test_proposal_rejects_unlocked_prereg` |
| 8 | Canonical JSON round-trips to identical hash | `tests/test_preregistration.py::test_canonical_json_determinism` |
| 9 | Locked prereg cannot be UPDATEd in Postgres | `tests/test_preregistration.py::test_locked_row_update_rejected` |
| 10 | Frozen paths hash lock detects drift | `tests/test_freeze_experiment.py::test_verify_detects_change` |
| 11 | `freeze verify` exits non-zero on drift | `tests/test_freeze_experiment.py::test_cli_exit_code` |
| 12 | Ethics Auditor rejects non-Opus model in verdict | `tests/test_ethics_auditor.py::test_verdict_validator_opus_only` |
| 13 | Auditor rejects when payload hits a REJECT rule | `tests/test_ethics_auditor.py::test_reject_on_banned_category` |
| 14 | Auditor is single-flight | `tests/test_ethics_auditor.py::test_concurrent_calls_serialized` |
| 15 | Cached verdict returned on re-submission | `tests/test_ethics_auditor.py::test_cached_reject_not_requeried` |
| 16 | Ruleset hash matches prompt file | `tests/test_ethics_auditor.py::test_ruleset_hash_matches_prompt_md` |
| 17 | Trust boundary: only Mother writes ledger | `tests/test_trust_boundary.py::test_non_mother_cannot_write_ledger` |
| 18 | Children cannot spawn children | `tests/test_trust_boundary.py::test_child_graph_has_no_spawn_node` |
| 19 | Sandbox blocks network | `tests/test_sandbox.py::test_sandbox_no_network` |
| 20 | Sandbox wall-clock enforced | `tests/test_sandbox.py::test_sandbox_timeout_300s` |
| 21 | Sandbox memory cap enforced | `tests/test_sandbox.py::test_sandbox_oom_at_512m` |
| 22 | Tool artifact sha256 is deterministic | `tests/test_tool_lifecycle.py::test_artifact_sha_determinism` |
| 23 | High-risk tool requires ethics approval | `tests/test_tool_lifecycle.py::test_high_risk_blocked_without_verdict` |
| 24 | Channel lint forbids ad-hoc httpx outside channels pkg | `tests/test_channels_lint.py::test_lint_flags_httpx_outside_channels` |
| 25 | Polar client signs requests with org token | `tests/test_channels_lint.py::test_polar_client_auth_header` |
| 26 | Model router downgrades when Operating < $100 | `tests/test_model_router.py::test_downgrade_below_100` |
| 27 | Ethics always uses Opus regardless of pot | `tests/test_model_router.py::test_ethics_uses_opus_always` |
| 28 | Budget enforcement pre-call | `tests/test_model_router.py::test_budget_exceeded_raises` |
| 29 | Operator parser: APPROVE happy path | `tests/test_operator_parser.py::test_approve_happy_path` |
| 30 | Operator parser: malformed message → form letter | `tests/test_operator_parser.py::test_malformed_rejected` |
| 31 | Expansion ladder rung 2 requires $100 + margin | `tests/test_expansion_ladder.py::test_rung2_gates` |
| 32 | Concentration rule: 1-channel halts new proposals | `tests/test_expansion_ladder.py::test_single_channel_halts_proposals` |
| 33 | Child auto-kill on 30d revenue miss | `tests/test_child_supervisor.py::test_auto_kill_on_day30_miss` |
| 34 | Child auto-pause on budget breach | `tests/test_child_supervisor.py::test_pause_on_monthly_budget` |
| 35 | Kill ALL completes within 30s in sim | `tests/test_kill_switch.py::test_kill_all_30s` |
| 36 | EMERGENCY_TRANSFER requires valid HMAC | `tests/test_kill_switch.py::test_emergency_transfer_hmac_required` |
| 37 | 14-day sim produces a valid weekly digest | `tests/integration/test_full_loop_sim.py::test_digest_fields` |
| 38 | Crash mid-loop → resume on restart | `tests/integration/test_full_loop_sim.py::test_crash_and_resume` |
| 39 | Gmail push delivers to `/webhooks/gmail` and parses | `tests/integration/test_gmail_roundtrip.py::test_push_parsed` |
| 40 | Frozen-hash drift raises `frozen_hash_drift=True` in next digest | `tests/integration/test_full_loop_sim.py::test_drift_flagged_in_digest` |

All 40 tests must pass.

---

## 21. Day 0 operator checklist

A one-time manual flow. After completion, the operator does not touch the system except for APPROVE/REJECT/CONTINUE/PAUSE/KILL.

1. **Legal entity.** Incorporate a US LLC via Stripe Atlas ($500 one-time + $100/yr registered agent). Alternative: Doola, Firstbase. Expect 2–14 days. Receive EIN.
2. **Banking.** Open Mercury (preferred) or Wise Business USD account under the LLC. Receive ACH routing + account.
3. **Platform accounts** (one-time per platform):
   - Polar.sh organization + API token (org-scoped).
   - Lemon Squeezy store + API key (fallback MoR).
   - Stripe account (Connect-enabled) under the LLC + `sk_live_...`.
   - Cloudflare account + API token (Workers Scripts:Edit, R2:Edit, Registrar:Edit).
   - Porkbun API key + secret.
   - Vercel Pro seat ($20/mo) + PAT.
   - Netlify account + PAT.
   - Anthropic API key with a $500 usage cap.
   - Google Cloud project + Gemini API key + Pub/Sub topic + service account for Pub/Sub.
   - Gmail OAuth2 consent + refresh token.
   - Langfuse Cloud account + public/secret keys.
4. **Infrastructure.** Provision Hetzner CX22 (or Railway Pro). Install Docker + gVisor. Clone repo. Populate `.env` from `.env.example`.
5. **Secrets.** Generate `OPERATOR_HMAC_SECRET` (32 bytes urlsafe) and store offline. This is what signs `EMERGENCY_TRANSFER`.
6. **Bootstrap.** `python scripts/day0_bootstrap.py` — runs migrations, seeds frozen hashes, pings every channel, sends test digest to operator inbox.
7. **Simulation run.** `AAE_MODE=simulation python -m aae.server.app` + wait for `test_full_loop_sim.py` gate to report GREEN. Verify digest received.
8. **Go live.** Flip `AAE_MODE=live` in `.env`. Fund Operating pot with $200 (manual Wire/ACH + `CashflowEntry` via `scripts/day0_bootstrap.py --seed-operating 200`). Restart.
9. **First proposal.** Wait ≤ 72h for the Mother to draft the first `VerticalProposal`. Review carefully. Reply `APPROVE <id>` or `REJECT <id>`.
10. **Tax readiness.** See §22. Register with PSEB if eligible; confirm with bank how Wise inflows are coded.

---

## 22. Pakistan taxation pointer

**This is not tax advice.** The V2.2 knowledge base flagged Pakistan tax exposure as a top risk. For an operator receiving digital-service inflows via Wise from a US LLC:

- Pakistani IT / IT-enabled services exports fall under the Final Tax Regime with a historical **1% WHT** on export remittances, reducible to **0.25% with PSEB registration**, codified at time of writing through **tax year 2026**. Confirm whether the Finance Act 2026 extends the concession.
- Wise inflows are treated as export remittances **only if** your Pakistani bank codes them with the correct purpose code (export of IT services). Operator must confirm with their bank and obtain a PRC (Proceeds Realisation Certificate) for each inflow.
- Section 65F 100% tax credit for IT exports has been time-boxed historically; verify current status directly.
- 50% of export proceeds may be retained in a foreign currency account per State Bank of Pakistan rules.
- **Operator must:** (a) register NTN via FBR IRIS, (b) apply for PSEB registration if eligible, (c) consult a qualified Pakistani tax professional about FY2026–27 applicability, (d) instruct their bank to correctly code Wise deposits.
- Authoritative sources (consult in order):
  - https://www.fbr.gov.pk
  - https://iris.fbr.gov.pk
  - https://www.pseb.org.pk
  - https://www.sbp.org.pk
  - Current Finance Act text (published by FBR each July).

This section is reproduced verbatim in `/aae/docs/tax_pointer.md` so the operator retains a permanent reference inside the repo.

---

## Conclusion — what this roadmap locks in

V3.0 is the point at which the Autonomous Agent Ecosystem graduates from a "supervised-ish multi-agent experiment" to a **genuinely autonomous revenue system with bounded human input**. The three pillars — zero-human-touch revenue (§6), profit-blind ethics review (§12), and frozen-config integrity (§11) — close the three failure modes that V2.2's review surfaced: operational dependence on the operator, ethics drift under profit pressure, and silent rewriting of safety rules.

The implementer should read §17 (directory tree) + §18 (build order) + §20 (acceptance tests) as the minimal spine: any other section is detail that supports those three artifacts. If all 40 tests in §20 pass and the 14-day sim (§19) clears, V3.0 is ready for the operator's Day 0 checklist (§21), and the system is launch-ready.

Two future risks deserve the operator's attention even after launch. First, **Cloudflare Registrar API** is still in beta as of April 2026 — track its GA and rate-limit changes; have Porkbun as a first-class fallback. Second, **Opus 4.7's new tokenizer** can silently inflate bills ~30% versus 4.6 despite identical rate cards — watch the Langfuse cost dashboard for the first two weeks and downgrade the Mother to Sonnet 4.6 if Opus cost grows disproportionately to output quality. Everything else in V3.0 is mechanically enforced; these two are judgment calls that belong on a post-launch review calendar.
