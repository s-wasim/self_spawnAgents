"""Cloudflare (Workers + R2 + Registrar) channel client (§6.3)."""
from __future__ import annotations

import time

import httpx

from aae.channels.base import BaseChannelClient, ChannelStatus


class CloudflareClient(BaseChannelClient):
    name = "cloudflare"
    base_url = "https://api.cloudflare.com/client/v4"

    def __init__(self, client: httpx.AsyncClient, *, api_token: str, account_id: str) -> None:
        super().__init__(client)
        self._token = api_token
        self._account_id = account_id

    def auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}

    async def health(self) -> ChannelStatus:
        t0 = time.monotonic()
        try:
            await self._get_json("/user/tokens/verify")
            return ChannelStatus(self.name, True, int((time.monotonic() - t0) * 1000))
        except httpx.HTTPError as e:
            return ChannelStatus(self.name, False, int((time.monotonic() - t0) * 1000), str(e))

    async def put_worker_script(self, *, name: str, body: str) -> dict:
        r = await self._client.put(
            f"{self.base_url}/accounts/{self._account_id}/workers/scripts/{name}",
            headers={**self.auth_headers(), "Content-Type": "application/javascript"},
            content=body.encode("utf-8"),
        )
        r.raise_for_status()
        return r.json()

    async def r2_put_object(self, *, bucket: str, key: str, body: bytes) -> None:
        r = await self._client.put(
            f"{self.base_url}/accounts/{self._account_id}/r2/buckets/{bucket}/objects/{key}",
            headers=self.auth_headers(),
            content=body,
        )
        r.raise_for_status()

    async def registrar_check_domain(self, *, name: str) -> dict:
        return await self._get_json(
            f"/accounts/{self._account_id}/registrar/domains/{name}"
        )

    async def registrar_register_domain(self, *, name: str, years: int) -> dict:
        return await self._post_json(
            f"/accounts/{self._account_id}/registrar/domains/{name}",
            {"years": years},
        )
