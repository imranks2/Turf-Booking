from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    FLASK_ENV: str = "development"
    SECRET_KEY: str
    JWT_SECRET: str
    FRONTEND_URL: str = "http://localhost:5173"

    DATABASE_URL: str
    REDIS_URL: str = "redis://redis:6379/0"

    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET: str = ""
    S3_REGION: str = "ap-south-1"

    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAYX_KEY_ID: str = ""
    RAZORPAYX_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""

    TWOFACTOR_API_KEY: str = ""
    GUPSHUP_API_KEY: str = ""
    GUPSHUP_APP_NAME: str = ""

    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    ACCESS_TOKEN_TTL_MINUTES: int = 15
    REFRESH_TOKEN_TTL_DAYS: int = 7
    PASSWORD_RESET_TTL_SECONDS: int = 3600
    SLOT_LOCK_TTL_SECONDS: int = 300
    BCRYPT_ROUNDS: int = 12

    RATE_LIMIT_IP_PER_MINUTE: int = 1000
    RATE_LIMIT_USER_PER_MINUTE: int = 300

    @property
    def is_production(self) -> bool:
        return self.FLASK_ENV == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
