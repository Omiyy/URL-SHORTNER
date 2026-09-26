from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator


RESERVED_SHORT_CODES = {
    "api",
    "auth",
    "docs",
    "health",
    "openapi.json",
    "redoc",
    "register",
    "login",
    "logout",
    "urls",
}


class CreateUrlRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    original_url: AnyHttpUrl
    custom_alias: str | None = Field(None, min_length=3, max_length=32)

    @field_validator("custom_alias")
    @classmethod
    def validate_custom_alias(cls, value: str | None) -> str | None:
        if value is None:
            return None

        alias = value.strip()

        if not alias:
            return None

        if not 3 <= len(alias) <= 32:
            raise ValueError("Custom alias must be between 3 and 32 characters")

        if alias.lower() in RESERVED_SHORT_CODES:
            raise ValueError("This custom alias is reserved")

        if not all(char.isalnum() or char in {"-", "_"} for char in alias):
            raise ValueError(
                "Custom alias may contain only letters, numbers, hyphens, and underscores"
            )

        return alias


class UrlResponse(BaseModel):
    short_code: str
    short_url: str
    original_url: str
    no_of_clicks: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UrlStatsResponse(BaseModel):
    short_code: str
    original_url: str
    no_of_clicks: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
