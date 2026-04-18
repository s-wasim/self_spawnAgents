# Autonomous Agent Ecosystem (AAE) — V3.0

Reference implementation of the AAE V3.0 spec defined in `AAE_V3_0_Roadmap.md`.
Four-agent, zero-human-touch autonomous revenue system:

1. **Mother Agent** — stateful LangGraph controller, three-pot cashflow.
2. **Code Builder** — stateless, sandboxed tool generator.
3. **Ethics Auditor** — profit-blind, Opus-4.7-only, frozen prompt.
4. **Child Agents** — per-vertical, capped-budget LangGraph instances.

## Quickstart (developer)

```bash
pip install -e .[dev]
pytest -q
python -m aae.ops.freeze_experiment verify
python scripts/lint_channels.py
```

## Day 0 (operator)

See §21 of `AAE_V3_0_Roadmap.md`. Summary:

1. Incorporate US LLC + open Mercury/Wise USD account.
2. Create platform accounts (Polar, LS, Stripe, Cloudflare, Porkbun, Vercel, Netlify, Anthropic, Google, Gmail, Langfuse).
3. Provision Hetzner CX22 with Docker + gVisor, populate `.env`.
4. Generate `OPERATOR_HMAC_SECRET` (32 bytes urlsafe).
5. `python scripts/day0_bootstrap.py` — migrate DB, seed frozen hashes, ping channels, send test digest.
6. `AAE_MODE=simulation` — wait for §19 gate GREEN.
7. Flip to `AAE_MODE=live` + fund Operating pot.
8. Reply `APPROVE <id>` to the first `VerticalProposal`.

## Operator-only verification

The following cannot be verified inside the CI sandbox; the operator must confirm them on the Hetzner host on Day 0:

- Real Docker + gVisor sandbox isolation (§9.3).
- LangGraph `PostgresSaver` checkpointing against Postgres 18.
- Live Anthropic / Gemini cost accounting.
- Real Gmail push → `/webhooks/gmail` round-trip (§14.3).
- Real channel API handshake (Polar / LS / Stripe / Cloudflare / Porkbun / Vercel / Netlify).

## Safety invariants

- **Zero-human-touch revenue** (§6).
- **Profit-blind ethics review** (§12).
- **Frozen-config integrity** (§11).

Frozen paths (any change trips the integrity alarm):

```
aae/ethics/prompt.md
aae/ethics/auditor.py
aae/cashflow/hard_floors.py
aae/config/frozen/expansion_rungs.py
aae/config/frozen/model_routing.py
aae/preregistration/schema.py
aae/preregistration/canonical.py
aae/core/trust_boundary.py
```

To legitimately change a frozen file: edit, run `aae-freeze update`, commit the updated `hashes.lock`, and append a signed note to `CHANGELOG.frozen.md` (§11.3).

## Kill switch

Email the operator inbox. Allowed verbs: `APPROVE`, `REJECT`, `CONTINUE`, `PAUSE`, `KILL <id>`, `KILL ALL`, `RESUME <event>`, `EMERGENCY_TRANSFER <amt> reserve->operating <hmac>`.

## Repository map

See §17 of the roadmap.
