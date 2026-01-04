from pydantic import BaseModel, EmailStr, Field
from models.users import User


class SignupRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=12)
    phone: int


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    user_id: str
    email: EmailStr
    username: str
    phone_number: int
    role: str
    is_blocked: bool

    @classmethod
    def from_domain(cls, user: User):
        return cls(
            user_id=user.user_id,
            email=user.email,
            username=user.username,
            phone_number=user.phone_number,
            role=user.role.value,
            is_blocked=user.is_blocked,
        )
