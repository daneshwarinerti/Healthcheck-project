"""
Dynamic configuration settings manager loaded based on the APP_ENV environment state.
"""

import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

# Determine target environment from environment variables (fallback to 'development')
app_env = os.getenv("APP_ENV", os.getenv("ENV_STATE", "development")).lower()
env_filename = f".env.{app_env}"

# If the targeted environment config file doesn't exist, check standard .env
if not os.path.exists(env_filename) and os.path.exists(".env"):
    env_filename = ".env"

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and config files.
    """
    APP_NAME: str = "Health Monitoring Dashboard"
    DATABASE_URL: str = "postgresql://postgres:postgres123@postgres:5432/healthdb"
    SECRET_KEY: str = "super-secret-key-development-only-change-this-in-production-123456"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    CORS_ORIGINS: List[str] = ["*"]

    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672

    USER_SERVICE_URL: str = "http://user-service:8001/health"
    PAYMENT_SERVICE_URL: str = "http://payment-service:8002/health"
    NOTIFICATION_SERVICE_URL: str = "http://notification-service:8003/health"

    model_config = SettingsConfigDict(
        env_file=env_filename,
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        # Prioritize system environment variables over local dotenv settings files
        return (init_settings, env_settings, dotenv_settings, file_secret_settings)

settings = Settings()
print(f"Config: Initialized settings using configuration file: '{env_filename}'")
print("Loaded Environment:", app_env)
print("Database URL:", settings.DATABASE_URL)
