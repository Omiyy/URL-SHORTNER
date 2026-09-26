import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]{3,30}$")


def normalize_user_name(value: str) -> str:
    user_name = value.strip()
    if not USERNAME_PATTERN.fullmatch(user_name):
        raise ValueError("Username may contain only letters, numbers, and underscores")
    return user_name.lower()

class RegisterRequest(BaseModel):
    user_name: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("user_name")
    @classmethod
    def validate_user_name(cls, value: str) -> str:
        return normalize_user_name(value)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if value.strip() != value:
            raise ValueError("Password cannot have leading or trailing whitespace")
        if not any(char.islower() for char in value):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(char.isupper() for char in value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain at least one digit")
        return value


class LoginRequest(BaseModel):
    user_name: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("user_name")
    @classmethod
    def normalize_user_name(cls, value: str) -> str:
        return normalize_user_name(value)


class UserResponse(BaseModel):
    user_id: UUID
    user_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
