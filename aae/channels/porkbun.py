"""Porkbun (domain fallback) channel client (§6.3)."""
from __future__ import annotations

import time

import httpx

from aae.channels.base import BaseChannelClient, ChannelStatus


class PorkbunClient(BaseChannelClient):
    name = "porkbun"
    base_url = "https://api.porkbun.com/api/json/v3"

    def __init__(self, client: httpx.AsyncClient, *, api_key: str, secret_key: str) -> None:
        super().__init__(client)
        self._api_key = api_key
        self._secret = secret_key

    def auth_headers(self) -> dict[str, str]:
        # Porkbun passes credentials in body, not headers; we still return JSON header.
        return {"Content-Type": "application/json"}

    def _creds(self) -> dict[str, str]:
        return {"apikey": self._api_key, "secretapikey": self._secret}

    async def health(self) -> ChannelStatus:
        t0 = time.monotonic()
        try:
            r = await self._client.post(
                f"{self.base_url}/ping",
                headers=self.auth_headers(),
                json=self._creds(),
            )
            r.raise_for_status()
            return ChannelStatus(self.name, True, int((time.monotonic() - t0) * 1000))
        except httpx.HTTPError as e:
            return ChannelStatus(self.name, False, int((time.monotonic() - t0) * 1000), str(e))

    async def check_domain(self, *, name: str) -> dict:
        return await self._post_json(
            f"/domain/checkDomain/{name}", {**self._creds()}
        )

    async def register_domain(self, *, name: str, years: int) -> dict:
        return await self._post_json(
            f"/domain/create/{name}", {**self._creds(), "years": years}
        )

    async def update_nameservers(self, *, name: str, ns: list[str]) -> dict:
        return await self._post_json(
            f"/domain/updateNs/{name}", {**self._creds(), "ns": ns}
        )
