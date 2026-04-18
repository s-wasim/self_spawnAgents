"""Vercel channel client (§6.3).

Hobby is forbidden for commercial use; `plan='pro'` required.
"""
from __future__ import annotations

import time

import httpx

from aae.channels.base import BaseChannelClient, ChannelStatus


class VercelClient(BaseChannelClient):
    name = "vercel"
    base_url = "https://api.vercel.com"

    def __init__(self, client: httpx.AsyncClient, *, pat: str, plan: str) -> None:
        super().__init__(client)
        self._pat = pat
        if plan != "pro":
            raise ValueError("Vercel plan must be 'pro' for commercial use")
        self._plan = plan

    def auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._pat}"}

    async def health(self) -> ChannelStatus:
        t0 = time.monotonic()
        try:
            await self._get_json("/v2/user")
            return ChannelStatus(self.name, True, int((time.monotonic() - t0) * 1000))
        except httpx.HTTPError as e:
            return ChannelStatus(self.name, False, int((time.monotonic() - t0) * 1000), str(e))

    async def create_project(self, *, name: str, framework: str | None = None) -> dict:
        return await self._post_json(
            "/v9/projects", {"name": name, "framework": framework}
        )

    async def create_deployment(self, *, project_id: str, files: dict) -> dict:
        return await self._post_json(
            "/v13/deployments", {"name": project_id, "files": files}
        )

    async def trigger_deploy_hook(self, *, hook_url: str) -> dict:
        r = await self._client.post(hook_url)
        r.raise_for_status()
        return r.json()
