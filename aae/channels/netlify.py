"""Netlify (hosting fallback) channel client (§6.3)."""
from __future__ import annotations

import time

import httpx

from aae.channels.base import BaseChannelClient, ChannelStatus


class NetlifyClient(BaseChannelClient):
    name = "netlify"
    base_url = "https://api.netlify.com/api/v1"

    def __init__(self, client: httpx.AsyncClient, *, pat: str) -> None:
        super().__init__(client)
        self._pat = pat

    def auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._pat}"}

    async def health(self) -> ChannelStatus:
        t0 = time.monotonic()
        try:
            await self._get_json("/user")
            return ChannelStatus(self.name, True, int((time.monotonic() - t0) * 1000))
        except httpx.HTTPError as e:
            return ChannelStatus(self.name, False, int((time.monotonic() - t0) * 1000), str(e))

    async def create_site(self, *, name: str) -> dict:
        return await self._post_json("/sites", {"name": name})

    async def upload_zip_deploy(self, *, site_id: str, zip_bytes: bytes) -> dict:
        r = await self._client.post(
            f"{self.base_url}/sites/{site_id}/deploys",
            headers={**self.auth_headers(), "Content-Type": "application/zip"},
            content=zip_bytes,
        )
        r.raise_for_status()
        return r.json()

    async def get_site_url(self, *, site_id: str) -> str:
        data = await self._get_json(f"/sites/{site_id}")
        return data.get("ssl_url") or data.get("url", "")
