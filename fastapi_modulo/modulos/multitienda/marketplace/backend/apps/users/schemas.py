from pydantic import BaseModel, field_validator
from enum import Enum
from typing import Optional

class UserType(str, Enum):
    superadmin = "superadmin"
    vendor = "vendor"
    customer = "customer"

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    user_type: UserType
    vendor_profile_id: Optional[int] = None
    two_factor_enabled: bool = False

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if "@" not in normalized or "." not in normalized.rsplit("@", 1)[-1]:
            raise ValueError("Correo electrónico inválido.")
        return normalized

class UserRead(BaseModel):
    id: int
    username: str
    email: str
    user_type: UserType
    vendor_profile_id: Optional[int] = None
    two_factor_enabled: bool = False

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if "@" not in normalized or "." not in normalized.rsplit("@", 1)[-1]:
            raise ValueError("Correo electrónico inválido.")
        return normalized

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str
