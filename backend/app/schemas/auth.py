from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import UserRole

_PHONE_RE = re.compile(r"^\+?[1-9]\d{9,14}$")


class RegisterSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    phone: str
    password: str = Field(min_length=8, max_length=128)
    role: UserRole
    name: str = Field(min_length=2, max_length=255)
    business_name: str | None = Field(default=None, max_length=255)

    @field_validator("phone")
    @classmethod
    def _validate_phone(cls, v: str) -> str:
        if not _PHONE_RE.match(v):
            raise ValueError("Invalid phone number")
        return v

    @field_validator("role")
    @classmethod
    def _no_admin_self_register(cls, v: UserRole) -> UserRole:
        if v == UserRole.saas_admin:
            raise ValueError("Cannot self-register as saas_admin")
        return v


class LoginSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class ForgotPasswordSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr


class ResetPasswordSchema(BaseModel):
    token: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    phone: str
    role: UserRole
    is_active: bool
    is_verified: bool
