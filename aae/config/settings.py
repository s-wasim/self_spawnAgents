"""Runtime settings (pydantic-settings)."""
from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    mode: Literal["simulation", "live"] = Field(default="simulation", alias="AAE_MODE")
    operator_email: str = Field(default="operator@example.com", alias="AAE_OPERATOR_EMAIL")
    postgres_dsn: str = Field(
        default="postgresql+psycopg://aae:aae@localhost:5432/aae", alias="POSTGRES_DSN"
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")

    polar_org_token: str = Field(default="", alias="POLAR_ORG_TOKEN")
    lemonsqueezy_api_key: str = Field(default="", alias="LEMONSQUEEZY_API_KEY")
    stripe_secret_key: str = Field(default="", alias="STRIPE_SECRET_KEY")
    cloudflare_api_token: str = Field(default="", alias="CLOUDFLARE_API_TOKEN")
    cloudflare_account_id: str = Field(default="", alias="CLOUDFLARE_ACCOUNT_ID")
    porkbun_api_key: str = Field(default="", alias="PORKBUN_API_KEY")
    porkbun_secret_api_key: str = Field(default="", alias="PORKBUN_SECRET_API_KEY")
    vercel_pat: str = Field(default="", alias="VERCEL_PAT")
    vercel_plan: str = Field(default="pro", alias="VERCEL_PLAN")
    netlify_pat: str = Field(default="", alias="NETLIFY_PAT")

    gmail_refresh_token: str = Field(default="", alias="GMAIL_OAUTH_REFRESH_TOKEN")
    gmail_client_id: str = Field(default="", alias="GMAIL_OAUTH_CLIENT_ID")
    gmail_client_secret: str = Field(default="", alias="GMAIL_OAUTH_CLIENT_SECRET")
    gcp_pubsub_topic: str = Field(default="", alias="GCP_PUBSUB_TOPIC")

    operator_hmac_secret: str = Field(default="", alias="OPERATOR_HMAC_SECRET")

    langfuse_public_key: str = Field(default="", alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str = Field(default="", alias="LANGFUSE_SECRET_KEY")
    langfuse_host: str = Field(default="https://cloud.langfuse.com", alias="LANGFUSE_HOST")

    # Derived defaults (not env-sourced).
    operating_default_topup_usd: Decimal = Decimal("200")


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
