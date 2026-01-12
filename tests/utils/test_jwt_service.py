import pytest
from datetime import datetime, timedelta, timezone
from jose import jwt

from utils.jwt_service import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    SECRET_KEY,
    create_jwt,
    decode_access_token,
)


def test_create_jwt_contains_claims_and_future_exp():
    now = datetime.now(timezone.utc)

    token = create_jwt(user_id="u1", email="a@b.com", role="admin")
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    assert payload["user_id"] == "u1"
    assert payload["email"] == "a@b.com"
    assert payload["role"] == "admin"

    exp_ts = payload["exp"]
    exp_dt = datetime.fromtimestamp(exp_ts, tz=timezone.utc)
    assert exp_dt > now
    assert exp_dt <= now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES + 1)


def test_decode_access_token_round_trip():
    token = create_jwt(user_id="u2", email="c@d.com", role="customer")

    payload = decode_access_token(token)

    assert payload["user_id"] == "u2"
    assert payload["email"] == "c@d.com"
    assert payload["role"] == "customer"


def test_decode_access_token_invalid_signature_raises():
    token = create_jwt(user_id="u3", email="x@y.com", role="host")
    tampered = token[:-1] + ("x" if token[-1] != "x" else "y")

    with pytest.raises(jwt.JWTError):
        decode_access_token(tampered)
