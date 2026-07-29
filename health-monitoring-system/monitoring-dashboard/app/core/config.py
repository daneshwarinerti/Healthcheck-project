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
    Application settings loaded from the environment-specific .env file.
    """
    APP_NAME: str = "Health Monitoring Dashboard"
    DATABASE_URL: str = "sqlite:///./health.db"
    SECRET_KEY: str = "super-secret-key-development-only-change-this-in-production-123456"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    CORS_ORIGINS: List[str] = ["*"]

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
        # Prioritize local dotenv settings files over global system environment variables
        return (init_settings, dotenv_settings, env_settings, file_secret_settings)

settings = Settings()
print(f"Config: Initialized settings using configuration file: '{env_filename}'")
print("Loaded Environment:", app_env)
print("Database URL:", settings.DATABASE_URL)
