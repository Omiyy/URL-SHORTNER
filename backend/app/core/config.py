from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FastURL"
    app_domain: str = "http://localhost:8000"

    database_url: str
    db_pool_size: int = 10
    db_max_overflow: int = 20

    frontend_origin: str = "http://localhost:5173"

    redis_url: str
    redis_cache_ttl_seconds: int = 3600
    redis_max_connections: int = 20
    redis_socket_timeout_seconds: float = 2.0
    click_flush_interval_seconds: int = 60
    deleted_url_retention_seconds: int = 86400

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    refresh_cookie_name: str = "refresh_token"
    refresh_cookie_secure: bool = False
    refresh_cookie_samesite: Literal["lax", "strict", "none"] = "lax"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
