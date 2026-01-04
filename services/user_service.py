from typing import Optional, Protocol
from models.users import User, Role
from repository.user_repository import UserRepository
from custom_exceptions.user_exceptions import (
    UserNotFoundError,
    IncorrectCredentials,
    UserAlreadyExists,
)
import bcrypt
import re
import uuid
from datetime import datetime, timedelta,UTC
from jose import jwt

SECRET_KEY = "your_very_secret_key" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 
def decode_access_token(token: str):
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


class UserServiceProtocol(Protocol):
    def get_user_by_id(self, user_id) -> Optional[User]:
        pass

    def get_user_by_mail(self, user) -> Optional[User]:
        pass

    def login(self, email, password) -> str:
        pass

    def signup(self) -> str:
        pass


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def get_user_by_id(self, user_id: str):
        user = self.user_repo.get_by_id(user_id=user_id)
        if user is None:
            raise UserNotFoundError(f"User not found with id {user_id}")
        return user

    def get_user_by_mail(self, mail):
        user = self.user_repo.get_by_mail(mail=mail)
        if user is None:
            raise UserNotFoundError(f"User not found with mail {mail}")
        return user

    def login(self, email: str, password: str) -> str:
        user = self.get_user_by_mail(email)

        if not bcrypt.checkpw(
            password.encode("utf-8"),
            user.password.encode("utf-8"),
        ):
            raise IncorrectCredentials("Invalid email or password")

        return self._create_jwt(user.user_id,email,user.role)

    def signup(self, email: str, username: str, password: str, phone: int) -> str:
        self._is_email_valid(email)
        self._is_password_valid(password)
        self._is_number_valid(phone)

        hashed = self._hash_password(password)
        user_id=str(uuid.uuid4())

        self.user_repo.add_user(
            User(
                user_id=user_id,
                username=username,
                email=email,
                phone_number=phone,
                password=hashed,
                role=Role.CUSTOMER,
                is_blocked=False,
            )
        )
        return self._create_jwt(user_id,email,"customer")

    def _is_number_valid(self, phone_number: int):
        s = str(phone_number)
        if not s.isdigit() or len(s) != 10:
            raise ValueError("Invalid phone number")

    def _is_password_valid(self, password: str):
        if len(password) < 12:
            raise ValueError("Password must be at least 12 characters")
        if not any(c.isupper() for c in password):
            raise ValueError("Password must contain uppercase letter")
        if not any(c.islower() for c in password):
            raise ValueError("Password must contain lowercase letter")
        if not any(c.isdigit() for c in password):
            raise ValueError("Password must contain digit")

    def _hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def _is_email_valid(self, email: str):
        pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(pattern, email):
            raise ValueError("Invalid email format")
        user = self.get_user_by_mail(email)
        if user:
            raise UserAlreadyExists("email is already in use")
        
    def _create_jwt(user_id: str, email: str, role: str):
        payload = {
            "user_id": user_id,
            "email": email,
            "role": role,
            "exp": datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return token
