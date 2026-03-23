"""Centralized configuration from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:pass@localhost:5432/templatemill"

    # Local Storage (for generated assets, mockups, exports)
    STORAGE_DIR: str = "./storage"
    STORAGE_CONTAINER: str = "templatemill"

    # API Keys
    ANTHROPIC_API_KEY: str = ""
    ETSY_API_KEY: str = "ul017toskhnfcfij7pr96uab"
    ETSY_SHARED_SECRET: str = "70vpmszkd1"
    ETSY_ACCESS_TOKEN: str = ""
    ETSY_REFRESH_TOKEN: str = ""
    PINTEREST_ACCESS_TOKEN: str = ""
    PINTEREST_APP_ID: str = ""
    PINTEREST_APP_SECRET: str = ""
    GUMROAD_ACCESS_TOKEN: str = ""
    SHOPIFY_STORE_URL: str = ""
    SHOPIFY_ACCESS_TOKEN: str = ""

    # Feature Flags
    ENABLE_TIKTOK_SCRAPING: bool = True
    ENABLE_PINTEREST_SCRAPING: bool = True
    ENABLE_COMPETITOR_MONITORING: bool = True

    # Scraping
    SCRAPE_HEADLESS: bool = True
    SCRAPE_MIN_DELAY: float = 2.0
    SCRAPE_MAX_DELAY: float = 5.0

    # Scoring
    OPPORTUNITY_ALERT_THRESHOLD: float = 75.0
    OPPORTUNITY_REVIEW_THRESHOLD: float = 50.0

    # Email
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    DIGEST_RECIPIENTS: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
