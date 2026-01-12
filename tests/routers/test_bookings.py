import pytest

from conftest import bookings_client_customer


def test_create_booking_calls_service(bookings_client_customer):
	client, booking_svc, user = bookings_client_customer
	payload = {"show_id": "s1", "seats": ["A1", "A2"]}

	resp = client.post("/bookings", json=payload)

	assert resp.status_code == 200
	body = resp.json()
	assert body["message"] == "succesfully made booking"
	assert len(booking_svc.create_calls) == 1
	req_obj, uid = booking_svc.create_calls[0]
	assert uid == user["user_id"]
	assert req_obj.show_id == "s1"
	assert req_obj.seats == ["A1", "A2"]


def test_create_booking_failure_surfaces(bookings_client_customer):
	client, booking_svc, user = bookings_client_customer
	booking_svc.create_exception = Exception("seat clash")

	resp = client.post("/bookings", json={"show_id": "s1", "seats": ["A1"]})

	assert resp.status_code == 500
	assert "seat clash" in resp.text
	assert len(booking_svc.create_calls) == 1
	req_obj, uid = booking_svc.create_calls[0]
	assert uid == user["user_id"]
	assert req_obj.show_id == "s1"
