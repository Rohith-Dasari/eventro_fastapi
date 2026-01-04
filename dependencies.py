from services.user_service import UserService
from repository.user_repository import UserRepository


def get_user_service() -> UserService:
    repo = UserRepository()
    return UserService(repo)
