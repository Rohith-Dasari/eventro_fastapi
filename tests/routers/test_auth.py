import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
APP_DIR = ROOT / "app"
if str(APP_DIR) not in sys.path:
	sys.path.insert(0, str(APP_DIR))

from conftest import auth_client
from custom_exceptions.user_exceptions import UserAlreadyExists, IncorrectCredentials
from custom_exceptions.generic import NotFoundException


def test_signup_returns_token_and_calls_service(auth_client):
	client_obj, service = auth_client
	payload = {
		"email": "a@b.com",
		"username": "alice",
		"password": "Sup3r$ecretPwd",
		"phone_number": "1234567890",
	}

	resp = client_obj.post("/signup", json=payload)

	assert resp.status_code == 201
	body = resp.json()
	assert body["message"] == "signup successful"
	assert body["data"] == service.signup_token
	assert service.signup_calls == [
		("a@b.com", "alice", "Sup3r$ecretPwd", "1234567890")
	]


def test_login_returns_token_and_calls_service(auth_client):
	client_obj, service = auth_client
	payload = {
		"email": "a@b.com",
		"password": "Sup3r$ecretPwd",
	}

	resp = client_obj.post("/login", json=payload)

	assert resp.status_code == 200
	body = resp.json()
	assert body["message"] == "login successful"
	assert body["data"] == service.login_token
	assert service.login_calls == [("a@b.com", "Sup3r$ecretPwd")]


def test_signup_user_already_exists(auth_client):
	client_obj, service = auth_client
	service.signup_exception = UserAlreadyExists("user exists")

	resp = client_obj.post(
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
	assert service.signup_calls == [
		("a@b.com", "alice", "Sup3r$ecretPwd", "1234567890")
	]


def test_login_incorrect_credentials(auth_client):
	client_obj, service = auth_client
	service.login_exception = IncorrectCredentials("invalid credentials")

	resp = client_obj.post(
		"/login",
		json={"email": "a@b.com", "password": "wrong"},
	)

	assert resp.status_code == 401
	assert "invalid credentials" in resp.text
	assert service.login_calls == [("a@b.com", "wrong")]


def test_login_user_not_found(auth_client):
	client_obj, service = auth_client
	service.login_exception = NotFoundException("user", "a@b.com", 404)

	resp = client_obj.post(
		"/login",
		json={"email": "a@b.com", "password": "any"},
	)

	assert resp.status_code == 404
	assert "user a@b.com not found" in resp.text
	assert service.login_calls == [("a@b.com", "any")]

