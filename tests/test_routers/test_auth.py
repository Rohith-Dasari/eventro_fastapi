import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_user_service
from unittest.mock import MagicMock
from app.custom_exceptions.generic import NotFoundException
from app.custom_exceptions.user_exceptions import (
    UserAlreadyExists,
    IncorrectCredentials,
)


class TestAuthRouter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        self.mock_get_user_service = MagicMock()
        app.dependency_overrides[get_user_service] = lambda: self.mock_get_user_service

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_signup_returns_token_and_calls_service(self):
        self.mock_get_user_service.signup.return_value = "Sup3r$ecretPwd"
        payload = {
            "email": "a@b.com",
            "username": "alice",
            "password": "Sup3r$ecretPwd",
            "phone_number": "1234567890",
        }

        resp = self.client.post("/signup", json=payload)

        assert resp.status_code == 201
        body = resp.json()
        assert body["message"] == "signup successful"
        assert body["data"] == "Sup3r$ecretPwd"

    def test_login_returns_token_and_calls_service(self):
        self.mock_get_user_service.login.return_value = "Sup3r$ecretPwd"
        payload = {
            "email": "a@b.com",
            "password": "Sup3r$ecretPwd",
        }

        resp = self.client.post("/login", json=payload)

        assert resp.status_code == 200
        body = resp.json()
        assert body["message"] == "login successful"
        assert body["data"] == "Sup3r$ecretPwd"

    def test_signup_user_already_exists(self):
        self.mock_get_user_service.signup.side_effect = UserAlreadyExists("user exists")

        resp = self.client.post(
            "/signup",
            json={
                "email": "a@b.com",
                "username": "alice",
                "password": "Sup3r$ecretPwd",
                "phone_number": "1234567890",
            },
        )

        assert resp.status_code == 400
        assert "user exists" in resp.text

    def test_login_incorrect_credentials(self):
        self.mock_get_user_service.login.side_effect = IncorrectCredentials(
            "invalid credentials"
        )

        resp = self.client.post(
            "/login",
            json={"email": "a@b.com", "password": "wrong"},
        )

        assert resp.status_code == 401
        assert "invalid credentials" in resp.text

    def test_login_user_not_found(self):
        self.mock_get_user_service.login.side_effect = NotFoundException(
            "user", "a@b.com", 404
        )

        resp = self.client.post(
            "/login",
            json={"email": "a@b.com", "password": "any"},
        )

        assert resp.status_code == 404
        assert "user a@b.com not found" in resp.text
