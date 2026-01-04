from dataclasses import dataclass
from enum import Enum


class Role(Enum):
    ADMIN = "admin"
    HOST = "host"
    CUSTOMER = "customer"


@dataclass
class User:
    user_id: str
    username: str
    email: str
    phone_number: str
    password: str
    role: Role
    is_blocked: bool


@dataclass
class UserDTO:
    user_id: str
    username: str
    email: str
    phone_number: str
    role: Role
    is_blocked: bool
