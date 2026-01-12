import sys
from pathlib import Path
import pytest
from fastapi import HTTPException

ROOT = Path(__file__).resolve().parent
APP_DIR = ROOT / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import dependencies as deps


def test_get_current_user_valid(monkeypatch):
    def fake_decode(token: str):
        return {"user_id": "u1", "role": "admin"}

    monkeypatch.setattr(deps, "decode_access_token", fake_decode)

    result = deps.get_current_user(token="good-token")

    assert result == {"user_id": "u1", "role": "admin"}


def test_get_current_user_invalid(monkeypatch):
    def fake_decode(token: str):
        raise Exception("bad token")

    monkeypatch.setattr(deps, "decode_access_token", fake_decode)

    with pytest.raises(HTTPException) as exc:
        deps.get_current_user(token="bad-token")

    assert exc.value.status_code == 401
    assert "Invalid or expired token" in exc.value.detail


def test_require_roles_allows_authorised_user():
    checker = deps.require_roles(["admin", "host"])
    user = {"user_id": "u1", "role": "admin"}

    result = checker(current_user=user)

    assert result is user


def test_require_roles_rejects_unauthorised_user():
    checker = deps.require_roles(["admin"])
    user = {"user_id": "u2", "role": "customer"}

    with pytest.raises(HTTPException) as exc:
        checker(current_user=user)

    assert exc.value.status_code == 403
    assert "unauthorised" in exc.value.detail
