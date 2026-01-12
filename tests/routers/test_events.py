import pytest

from conftest import (
	events_client_admin,
	events_client_customer,
	events_client_customer_forbidden,
)


def test_create_event_calls_service(events_client_admin):
	client, event_svc, user = events_client_admin
	payload = {
		"name": "Concert",
		"description": "Live",
		"duration": 120,
		"category": "movie",
		"artist_ids": ["a1", "a2"],
	}

	resp = client.post("/events", json=payload)

	assert resp.status_code == 201
	assert event_svc.create_calls == [
		("Concert", "Live", 120, "movie", ["a1", "a2"])
	]
	assert resp.json()["data"] == {"id": "e-created"}


def test_get_event_by_id_calls_service(events_client_customer):
	client, event_svc, user = events_client_customer

	resp = client.get("/events/e1")

	assert resp.status_code == 200
	assert event_svc.get_calls == [("e1", user["role"])]


def test_browse_events_requires_name_or_city(events_client_customer):
	client, _, _ = events_client_customer

	resp = client.get("/events")

	assert resp.status_code == 422
	assert "At least one of 'name' or 'city'" in resp.text


def test_browse_events_city_branch(events_client_customer):
	client, event_svc, user = events_client_customer

	resp = client.get("/events", params={"city": "NYC", "is_blocked": True})

	assert resp.status_code == 200
	assert event_svc.browse_city_calls == [("NYC", True, user["role"])]


def test_browse_events_name_branch(events_client_customer):
	client, event_svc, user = events_client_customer

	resp = client.get("/events", params={"name": "Rock", "city": "NYC"})

	assert resp.status_code == 200
	assert event_svc.browse_name_calls == [("Rock", "NYC", user["role"])]


def test_update_event_calls_service(events_client_admin):
	client, event_svc, _ = events_client_admin

	resp = client.patch("/events/e1", json={"is_blocked": True})

	assert resp.status_code == 200
	assert event_svc.update_calls
	event_id, update_req = event_svc.update_calls[0]
	assert event_id == "e1"
	assert update_req.is_blocked is True


def test_create_event_forbidden_role(events_client_customer_forbidden):
	client, _, _ = events_client_customer_forbidden

	resp = client.post(
		"/events",
		json={
			"name": "Concert",
			"description": "Live",
			"duration": 120,
			"category": "movie",
			"artist_ids": ["a1"],
		},
	)

	assert resp.status_code == 403
	assert "unauthorised" in resp.text


def test_get_event_not_found_uses_handler(events_client_customer):
	client, event_svc, user = events_client_customer
	event_svc.not_found_ids = {"missing"}

	resp = client.get("/events/missing")

	assert resp.status_code == 404
	assert "missing" in resp.text
	assert event_svc.get_calls == [("missing", user["role"])]


def test_browse_events_name_branch_invokes_service(events_client_customer):
	client, event_svc, user = events_client_customer

	resp = client.get("/events", params={"name": "Rock"})

	assert resp.status_code == 200
	assert event_svc.browse_name_calls == [("Rock", None, user["role"])]
