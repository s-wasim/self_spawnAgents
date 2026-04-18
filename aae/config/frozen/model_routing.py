"""Model routing tier table (§13.1). FROZEN."""
from __future__ import annotations

from decimal import Decimal

from aae.schemas.common import ModelID

# Per-million-token prices (USD) for input / output.
PRICE_TABLE: dict[ModelID, tuple[Decimal, Decimal]] = {
    ModelID.OPUS_47:              (Decimal("5.00"),  Decimal("25.00")),
    ModelID.SONNET_46:            (Decimal("3.00"),  Decimal("15.00")),
    ModelID.HAIKU_45:             (Decimal("1.00"),  Decimal("5.00")),
    ModelID.GEMINI_FLASH_LITE_25: (Decimal("0.10"),  Decimal("0.40")),
}

CONTEXT_WINDOWS: dict[ModelID, int] = {
    ModelID.OPUS_47:              1_000_000,
    ModelID.SONNET_46:            1_000_000,
    ModelID.HAIKU_45:                200_000,
    ModelID.GEMINI_FLASH_LITE_25: 1_000_000,
}

# §13.2 Mother downgrade threshold.
OPERATING_LOW_WATER_MARK_USD = Decimal("100")

# Batch API discount and cache-read discount (Anthropic).
BATCH_DISCOUNT = Decimal("0.50")
CACHE_READ_DISCOUNT = Decimal("0.90")
