"""Stripe Connect Custom channel client (§6.3)."""
from __future__ import annotations

import time
from decimal import Decimal

import httpx

from aae.channels.base import BaseChannelClient, ChannelStatus


class StripeConnectClient(BaseChannelClient):
    name = "stripe_connect"
    base_url = "https://api.stripe.com/v1"

    def __init__(self, client: httpx.AsyncClient, *, secret_key: str) -> None:
        super().__init__(client)
        self._secret = secret_key
        if not (secret_key.startswith("sk_live_") or secret_key.startswith("sk_test_") or secret_key == ""):
            raise ValueError("Stripe secret must start with sk_live_ or sk_test_")

    def auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._secret}"}

    async def health(self) -> ChannelStatus:
        t0 = time.monotonic()
        try:
            r = await self._client.get(
                f"{self.base_url}/balance",
                headers=self.auth_headers(),
            )
            r.raise_for_status()
            return ChannelStatus(self.name, True, int((time.monotonic() - t0) * 1000))
        except httpx.HTTPError as e:
            return ChannelStatus(self.name, False, int((time.monotonic() - t0) * 1000), str(e))

    async def create_custom_account(self, *, country: str, email: str) -> dict:
        r = await self._client.post(
            f"{self.base_url}/accounts",
            headers=self.auth_headers(),
            data={"type": "custom", "country": country, "email": email},
        )
        r.raise_for_status()
        return r.json()

    async def create_account_link(self, *, account: str, refresh_url: str, return_url: str) -> dict:
        r = await self._client.post(
            f"{self.base_url}/account_links",
            headers=self.auth_headers(),
            data={
                "account": account,
                "refresh_url": refresh_url,
                "return_url": return_url,
                "type": "account_onboarding",
            },
        )
        r.raise_for_status()
        return r.json()

    async def create_payment_intent(self, *, amount_usd: Decimal, connected_account: str) -> dict:
        r = await self._client.post(
            f"{self.base_url}/payment_intents",
            headers={**self.auth_headers(), "Stripe-Account": connected_account},
            data={"amount": int(amount_usd * 100), "currency": "usd"},
        )
        r.raise_for_status()
        return r.json()

    async def create_transfer(self, *, amount_usd: Decimal, destination: str) -> dict:
        r = await self._client.post(
            f"{self.base_url}/transfers",
            headers=self.auth_headers(),
            data={
                "amount": int(amount_usd * 100),
                "currency": "usd",
                "destination": destination,
            },
        )
        r.raise_for_status()
        return r.json()

    async def create_payout(self, *, amount_usd: Decimal, connected_account: str) -> dict:
        r = await self._client.post(
            f"{self.base_url}/payouts",
            headers={**self.auth_headers(), "Stripe-Account": connected_account},
            data={"amount": int(amount_usd * 100), "currency": "usd"},
        )
        r.raise_for_status()
        return r.json()
