"""Polar.sh MoR channel client (§6.3)."""
from __future__ import annotations

import time
from decimal import Decimal

import httpx

from aae.channels.base import BaseChannelClient, ChannelStatus


class PolarClient(BaseChannelClient):
    name = "polar"
    base_url = "https://api.polar.sh/v1"

    def __init__(self, client: httpx.AsyncClient, *, org_token: str) -> None:
        super().__init__(client)
        self._token = org_token

    def auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}

    async def health(self) -> ChannelStatus:
        t0 = time.monotonic()
        try:
            await self._get_json("/organizations/me")
            return ChannelStatus(self.name, True, int((time.monotonic() - t0) * 1000))
        except httpx.HTTPError as e:
            return ChannelStatus(self.name, False, int((time.monotonic() - t0) * 1000), str(e))

    async def create_product(self, *, name: str, price_usd: Decimal, is_recurring: bool) -> dict:
        payload = {
            "name": name,
            "prices": [{
                "amount_cents": int(price_usd * 100),
                "currency": "USD",
                "type": "recurring" if is_recurring else "one_time",
            }],
        }
        return await self._post_json("/products", payload)

    async def create_checkout(self, *, product_id: str, success_url: str) -> dict:
        return await self._post_json(
            "/checkouts", {"product_id": product_id, "success_url": success_url}
        )

    async def list_payouts(self) -> dict:
        return await self._get_json("/payouts")

    async def webhook_verify(self, *, signature: str, body: bytes, secret: str) -> bool:
        import hashlib
        import hmac
        want = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(want, signature)
