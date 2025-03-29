import os
from pydantic import PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    pg_dsn: PostgresDsn = os.getenv("DB_URL")
    redis_dsn: RedisDsn = os.getenv("REDIS_URL")
    applicant_bot_token: str = os.getenv("APPLICANT_BOT_TOKEN")
    employer_bot_token: str = os.getenv("EMPLOYER_BOT_TOKEN")
    admin_bot_token: str = os.getenv("ADMIN_BOT_TOKEN")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
