import unittest
from unittest.mock import MagicMock, patch

import bcrypt

from app.services.user_service import UserService
from app.models.users import User, Role
from app.custom_exceptions.generic import NotFoundException
from app.custom_exceptions.user_exceptions import (
    IncorrectCredentials,
    UserAlreadyExists,
    UserBlocked,
)


class TestUserService(unittest.TestCase):

    def setUp(self):
        self.mock_user_repo = MagicMock()
        self.user_service = UserService(self.mock_user_repo)

    def test_get_user_by_id_success(self):
        user = User(
            user_id="u1",
            username="test",
            email="a@b.com",
            phone_number="9999999999",
            password="hashed",
            role=Role.CUSTOMER,
            is_blocked=False,
        )
        self.mock_user_repo.get_by_id.return_value = user

        result = self.user_service.get_user_by_id("u1")

        assert result == user
        self.mock_user_repo.get_by_id.assert_called_once_with(user_id="u1")

    def test_get_user_by_id_not_found(self):
        self.mock_user_repo.get_by_id.return_value = None

        with self.assertRaises(NotFoundException):
            self.user_service.get_user_by_id("missing")

    def test_get_user_profile_maps_domain(self):
        user = User(
            user_id="u1",
            username="test",
            email="a@b.com",
            phone_number="9999999999",
            password="hashed",
            role=Role.CUSTOMER,
            is_blocked=False,
        )
        self.mock_user_repo.get_by_id.return_value = user

        profile = self.user_service.get_user_profile("u1")

        assert profile.user_id == "u1"
        assert profile.email == "a@b.com"

    def test_get_user_by_mail_success(self):
        user = MagicMock()
        self.mock_user_repo.get_by_mail.return_value = user

        result = self.user_service.get_user_by_mail("a@b.com")

        assert result == user

    def test_get_user_by_mail_not_found(self):
        self.mock_user_repo.get_by_mail.return_value = None

        with self.assertRaises(NotFoundException):
            self.user_service.get_user_by_mail("a@b.com")

    @patch("app.services.user_service.create_jwt")
    def test_login_success(self, mock_create_jwt):
        password = "StrongPassword!123"
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        user = User(
            user_id="u1",
            username="test",
            email="a@b.com",
            phone_number="9999999999",
            password=hashed,
            role=Role.CUSTOMER,
            is_blocked=False,
        )

        self.mock_user_repo.get_by_mail.return_value = user
        mock_create_jwt.return_value = "jwt-token"

        token = self.user_service.login("a@b.com", password)

        assert token == "jwt-token"
        mock_create_jwt.assert_called_once_with("u1", "a@b.com", "customer")

    def test_login_incorrect_password(self):
        user = User(
            user_id="u1",
            username="test",
            email="a@b.com",
            phone_number="9999999999",
            password=bcrypt.hashpw(b"CorrectPass!123", bcrypt.gensalt()).decode(),
            role=Role.CUSTOMER,
            is_blocked=False,
        )
        self.mock_user_repo.get_by_mail.return_value = user

        with self.assertRaises(IncorrectCredentials):
            self.user_service.login("a@b.com", "WrongPassword!123")

    @patch("app.services.user_service.create_jwt")
    def test_signup_success(self, mock_create_jwt):
        self.mock_user_repo.get_by_mail.return_value = None
        mock_create_jwt.return_value = "jwt-token"

        token = self.user_service.signup(
            email="user@test.com",
            username="user",
            password="StrongPass!123",
            phone="9876543210",
        )

        assert token == "jwt-token"
        self.mock_user_repo.add_user.assert_called_once()
        mock_create_jwt.assert_called_once()

    def test_signup_invalid_email(self):
        with self.assertRaises(ValueError):
            self.user_service.signup(
                email="bad-email",
                username="user",
                password="StrongPass!123",
                phone="9876543210",
            )

    def test_signup_invalid_password(self):
        self.mock_user_repo.get_by_mail.return_value = None

        with self.assertRaises(ValueError):
            self.user_service.signup(
                email="user@test.com",
                username="user",
                password="weak",
                phone="9876543210",
            )

    def test_signup_invalid_phone(self):
        self.mock_user_repo.get_by_mail.return_value = None

        with self.assertRaises(ValueError):
            self.user_service.signup(
                email="user@test.com",
                username="user",
                password="StrongPass!123",
                phone="123",
            )

    def test_signup_duplicate_email(self):
        self.mock_user_repo.get_by_mail.return_value = MagicMock()

        with self.assertRaises(UserAlreadyExists):
            self.user_service.signup(
                email="user@test.com",
                username="user",
                password="StrongPass!123",
                phone="9876543210",
            )

    def test_login_blocked_user(self):
        password = "StrongPass!123"
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        user = User(
            user_id="u1",
            username="test",
            email="a@b.com",
            phone_number="9999999999",
            password=hashed,
            role=Role.CUSTOMER,
            is_blocked=True,
        )

        self.mock_user_repo.get_by_mail.return_value = user

        with self.assertRaises(UserBlocked):
            self.user_service.login("a@b.com", password)
