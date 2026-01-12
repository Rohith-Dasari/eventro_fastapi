from pydantic import BaseModel, EmailStr, Field, field_validator
from models.users import User
import re

PASSWORD_REGEX = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{12,}$")


class SignupRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=30)
    phone_number: str = Field(min_length=10,max_length=10)
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str):
        if not PASSWORD_REGEX.fullmatch(v):
            raise ValueError(
                "Password must be at least 12 characters long and contain "
                "uppercase, lowercase, digit, and special character"
            )
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# class UserResponse(BaseModel):
#     user_id: str
#     email: EmailStr
#     username: str
#     phone_number: int
#     role: str
#     is_blocked: bool

#     @classmethod
#     def from_domain(cls, user: User):
#         return cls(
#             user_id=user.user_id,
#             email=user.email,
#             username=user.username,
#             phone_number=user.phone_number,
#             role=user.role.value,
#             is_blocked=user.is_blocked,
#         )
