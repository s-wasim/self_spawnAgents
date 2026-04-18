"""Pre-registration schema re-export (§4.6). FROZEN.

The single source of truth is aae.schemas.preregistration. This module re-exports
it so the frozen-path registry can pin /aae/preregistration/schema.py without
duplicating the class definition.
"""
from __future__ import annotations

from aae.schemas.preregistration import PreRegistration

__all__ = ["PreRegistration"]
