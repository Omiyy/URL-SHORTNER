from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FastURL"
    app_domain: str = "http://localhost"
    frontend_origin: str = "http://localhost"
    app_env: str = "development"

    database_url: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/url_shortener"
    db_pool_size: int = 20
    db_max_overflow: int = 40

    redis_url: str = "redis://redis:6379/0"
    redis_cache_ttl_seconds: int = 3600
    click_flush_interval_seconds: int = 60

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
