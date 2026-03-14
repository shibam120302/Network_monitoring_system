"""Application configuration."""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # App
    APP_NAME: str = "Network Monitoring System"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql://monitor:monitor@localhost:5432/network_monitoring"
    DATABASE_ASYNC_URL: str = "postgresql+asyncpg://monitor:monitor@localhost:5432/network_monitoring"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"

    # SMTP (Alerts)
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "alerts@network-monitor.local"
    ALERT_EMAIL_TO: str = "admin@example.com"

    # OpenAI / LLM
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    USE_LOCAL_LLM: bool = False
    LOCAL_LLM_BASE_URL: str = "http://localhost:11434/v1"  # Ollama

    # Monitoring thresholds (rule-based detection)
    THRESHOLD_LATENCY_MS: float = 100.0
    THRESHOLD_PACKET_LOSS_PCT: float = 5.0
    THRESHOLD_CPU_PCT: float = 90.0
    THRESHOLD_MEMORY_PCT: float = 90.0

    # Agent
    METRICS_INTERVAL_SEC: int = 30
    CENTRAL_API_URL: str = "http://localhost:8000"

    # Netmiko (remediation)
    NETMIKO_TIMEOUT: int = 30
    NETMIKO_DEVICE_TYPE: str = "cisco_ios"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
