"""Application configuration loaded from environment / .env via pydantic-settings."""
from __future__ import annotations

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- secrets / required ---
    telegram_bot_token: str
    anthropic_api_key: str
    auth_codeword: str

    # --- access control ---
    # Kept as raw string: pydantic-settings JSON-decodes list-typed fields at the
    # env-source level, which rejects "1,2". Parse it ourselves via the property.
    admin_ids_raw: str = Field(
        default="", validation_alias=AliasChoices("ADMIN_IDS", "admin_ids")
    )

    # --- model ---
    model: str = "claude-sonnet-4-6"

    # --- limits ---
    max_image_mb: int = 10
    task_timeout_sec: int = 600
    max_concurrent_tasks: int = 3

    # --- image diagnostics ---
    img_tile_grid: int = 3
    img_diff_threshold: float = 0.15
    img_max_iters: int = 3

    # --- storage ---
    db_path: str = "data/auth.db"

    @property
    def admin_ids(self) -> list[int]:
        """ADMIN_IDS as comma/space separated ids (also accepts a JSON list)."""
        raw = self.admin_ids_raw.strip()
        if not raw:
            return []
        if raw.startswith("["):
            import json

            return [int(x) for x in json.loads(raw)]
        return [int(p) for p in raw.replace(",", " ").split()]

    @property
    def max_image_bytes(self) -> int:
        return self.max_image_mb * 1024 * 1024


settings = Settings()  # type: ignore[call-arg]
