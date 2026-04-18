"""Base class for every channel client (§6.3).

Every channel adapter subclasses BaseChannelClient. The lint script forbids
direct httpx/requests usage outside this package, so this is the single place
HTTP calls to revenue/hosting/domain providers happen.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import httpx


@dataclass
class ChannelStatus:
    name: str
    ok: bool
    latency_ms: int
    detail: str = ""


class BaseChannelClient(ABC):
    name: str
    base_url: str

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    @abstractmethod
    def auth_headers(self) -> dict[str, str]: ...

    @abstractmethod
    async def health(self) -> ChannelStatus: ...

    async def _get_json(self, path: str, **kw) -> dict:
        r = await self._client.get(
            f"{self.base_url.rstrip('/')}/{path.lstrip('/')}",
            headers=self.auth_headers(),
            **kw,
        )
        r.raise_for_status()
        return r.json()

    async def _post_json(self, path: str, json: dict, **kw) -> dict:
        r = await self._client.post(
            f"{self.base_url.rstrip('/')}/{path.lstrip('/')}",
            headers=self.auth_headers(),
            json=json,
            **kw,
        )
        r.raise_for_status()
        return r.json()
