"""Lemon Squeezy (fallback MoR) channel client (§6.3)."""
from __future__ import annotations

import time
from decimal import Decimal

import httpx

from aae.channels.base import BaseChannelClient, ChannelStatus


class LemonSqueezyClient(BaseChannelClient):
    name = "lemonsqueezy"
    base_url = "https://api.lemonsqueezy.com/v1"

    def __init__(self, client: httpx.AsyncClient, *, api_key: str) -> None:
        super().__init__(client)
        self._api_key = api_key

    def auth_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
        }

    async def health(self) -> ChannelStatus:
        t0 = time.monotonic()
        try:
            await self._get_json("/users/me")
            return ChannelStatus(self.name, True, int((time.monotonic() - t0) * 1000))
        except httpx.HTTPError as e:
            return ChannelStatus(self.name, False, int((time.monotonic() - t0) * 1000), str(e))

    async def create_product(self, *, name: str, store_id: str) -> dict:
        return await self._post_json(
            "/products",
            {"data": {"type": "products", "attributes": {"name": name}, "relationships": {
                "store": {"data": {"type": "stores", "id": store_id}}
            }}}
        )

    async def create_variant(self, *, product_id: str, price_usd: Decimal) -> dict:
        return await self._post_json(
            "/variants",
            {"data": {"type": "variants",
                      "attributes": {"price": int(price_usd * 100)},
                      "relationships": {"product": {"data": {"type": "products", "id": product_id}}}}}
        )

    async def create_checkout(self, *, variant_id: str, store_id: str) -> dict:
        return await self._post_json(
            "/checkouts",
            {"data": {"type": "checkouts", "relationships": {
                "variant": {"data": {"type": "variants", "id": variant_id}},
                "store": {"data": {"type": "stores", "id": store_id}},
            }}},
        )

    async def list_subscriptions(self) -> dict:
        return await self._get_json("/subscriptions")

    async def webhook_verify(self, *, signature: str, body: bytes, secret: str) -> bool:
        import hashlib
        import hmac
        want = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(want, signature)
