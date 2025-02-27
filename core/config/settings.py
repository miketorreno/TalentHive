from pydantic import BaseSettings, PostgresDsn, RedisDsn


class Settings(BaseSettings):
    pg_dsn: PostgresDsn = "postgresql+asyncpg://user:pass@localhost/app"
    redis_dsn: RedisDsn = "redis://localhost:6379/0"
    applicant_bot_token: str
    employer_bot_token: str
    admin_bot_token: str

    class Config:
        env_file = ".env"


settings = Settings()
