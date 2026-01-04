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


class UserServiceProtocol(Protocol):
    def get_user_by_id(self, user_id) -> Optional[User]:
        pass

    def get_user_by_mail(self, user) -> Optional[User]:
        pass

    def login(self, email, password) -> Optional[User]:
        pass

    def signup(self) -> Optional[User]:
        pass


# what dshould i pass while signup


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

    def login(self, email: str, password: str) -> User:
        user = self.get_user_by_mail(email)

        if not bcrypt.checkpw(
            password.encode("utf-8"),
            user.password.encode("utf-8"),
        ):
            raise IncorrectCredentials("Invalid email or password")

        return user

    def signup(self, email: str, username: str, password: str, phone: int) -> User:
        self._is_email_valid(email)
        self._is_password_valid(password)
        self._is_number_valid(phone)

        hashed = self._hash_password(password)

        return self.user_repo.add_user(
            User(
                user_id=str(uuid.uuid4()),
                username=username,
                email=email,
                phone_number=phone,
                password=hashed,
                role=Role.CUSTOMER,
                is_blocked=False,
            )
        )

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
