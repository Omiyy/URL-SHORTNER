from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field


class ShortenRequest(BaseModel):
    url: AnyHttpUrl
    custom_alias: str | None = Field(default=None, min_length=3, max_length=20)
    expires_in_days: int | None = Field(default=None, ge=1, le=3650)


class ShortenResponse(BaseModel):
    short_url: str
    short_code: str


class StatsResponse(BaseModel):
    original_url: str
    clicks: int
    created_at: datetime
    last_accessed: datetime | None
    expires_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
