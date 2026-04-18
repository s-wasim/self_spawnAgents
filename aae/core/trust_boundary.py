"""Trust boundary (§5). FROZEN.

Enforced in code, not in prompts. Any violation triggers a hard stop (§5.2).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from aae.schemas.common import AgentTier


class TrustViolation(Exception):
    """Raised when any §5.1 rule is broken."""


class SystemState(str, Enum):
    NORMAL = "normal"
    HARD_STOP = "hard_stop"


@dataclass(frozen=True)
class SecurityEvent:
    rule: str
    detail: str


# Rule 1: only the Mother may write to cashflow_ledger.
MOTHER_ONLY_WRITERS: frozenset[AgentTier] = frozenset({AgentTier.MOTHER})

# Rule 6: Children have no spawn/dispatch_build nodes in their LangGraph.
CHILD_FORBIDDEN_NODES: frozenset[str] = frozenset(
    {"dispatch_build", "spawn_child", "write_cashflow", "request_ethics"}
)

# Rule 8: only /aae/channels/ may import httpx or requests.
CHANNELS_PACKAGE = "aae.channels"


def require_mother_for_ledger(tier: AgentTier) -> None:
    if tier not in MOTHER_ONLY_WRITERS:
        raise TrustViolation(
            f"Only the Mother Agent may write to cashflow_ledger; got {tier.value}"
        )


def assert_child_graph_allowed(nodes: set[str]) -> None:
    forbidden = nodes & CHILD_FORBIDDEN_NODES
    if forbidden:
        raise TrustViolation(
            f"Child graph contains forbidden nodes: {sorted(forbidden)}"
        )


def assert_no_network_in_builder(network_required: bool) -> None:
    if network_required:
        raise TrustViolation(
            "Code Builder sandbox has --network=none; network_required tools must be "
            "promoted to medium/high risk and executed via the tool-registry runtime."
        )
