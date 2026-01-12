import pytest

from conftest import users_client, fake_current_user_customer


def test_get_user_profile_returns_profile(users_client):
	client_obj, user_svc, _ = users_client

	resp = client_obj.get("/users/u-any")

	assert resp.status_code == 200
	body = resp.json()
	assert body["message"] == "succesfully retrieved user bookings"
	assert body["data"] == {"id": fake_current_user_customer()["user_id"], "username": "alice"}
	assert user_svc.profile_calls == [fake_current_user_customer()["user_id"]]


def test_get_user_bookings_returns_list(users_client):
	client_obj, _, booking_svc = users_client

	resp = client_obj.get("/users/u-any/bookings")

	assert resp.status_code == 200
	body = resp.json()
	assert body["message"] == "succesfully retrieved user bookings"
	assert len(body["data"]) == 2
	assert booking_svc.booking_calls == [fake_current_user_customer()["user_id"]]
