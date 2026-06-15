"""Provide dummy env so importing config.Settings does not fail in CI."""
import os

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("AUTH_CODEWORD", "open-sesame")
os.environ.setdefault("ADMIN_IDS", "1,2")
