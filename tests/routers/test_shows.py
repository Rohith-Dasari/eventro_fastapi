import pytest

from conftest import shows_client_host, shows_client_customer


def test_create_show_calls_service(shows_client_host):
	client, show_svc, user = shows_client_host
	payload = {
		"event_id": "e1",
		"venue_id": "v1",
		"price": 100,
		"show_date": "2024-01-01",
		"show_time": "19:00",
	}

	resp = client.post("/shows", json=payload)

	assert resp.status_code == 201
	assert resp.json()["message"] == "created show successfully"
	assert len(show_svc.create_calls) == 1
	show_dto = show_svc.create_calls[0]
	assert show_dto.event_id == "e1"
	assert show_dto.venue_id == "v1"


def test_get_show_by_id_calls_service(shows_client_customer):
	client, show_svc, _ = shows_client_customer

	resp = client.get("/shows/s1")

	assert resp.status_code == 200
	assert show_svc.get_calls == ["s1"]


def test_get_show_by_id_not_found(shows_client_customer):
	client, show_svc, _ = shows_client_customer
	show_svc.not_found_ids.add("missing")

	resp = client.get("/shows/missing")

	assert resp.status_code == 404
	assert "show missing not found" in resp.text
	assert show_svc.get_calls == ["missing"]


def test_event_shows_host_id_mismatch_returns_forbidden_body(shows_client_customer):
	client, show_svc, user = shows_client_customer

	resp = client.get(
		"/shows",
		params={"event_id": "e1", "city": "NYC", "host_id": "h1"},
	)
	body = resp.json()

	assert resp.status_code == 200
	assert body["status_code"] == 403
	assert "forbidden" in body["message"]
	assert show_svc.list_calls == []


def test_event_shows_host_match_calls_service(shows_client_host):
	client, show_svc, user = shows_client_host

	resp = client.get(
		"/shows",
		params={"event_id": "e1", "city": "NYC", "host_id": "h1"},
	)

	assert resp.status_code == 200
	assert show_svc.list_calls == [("e1", "nyc", user, None)]


def test_event_shows_customer_calls_service(shows_client_customer):
	client, show_svc, user = shows_client_customer

	resp = client.get(
		"/shows",
		params={"event_id": "e1", "city": "NYC"},
	)

	assert resp.status_code == 200
	assert show_svc.list_calls == [("e1", "nyc", user, None)]


def test_update_show_calls_service(shows_client_host):
	client, show_svc, _ = shows_client_host

	resp = client.patch("/shows/s1", json={"is_blocked": True})

	assert resp.status_code == 200
	assert len(show_svc.update_calls) == 1
	show_id, req = show_svc.update_calls[0]
	assert show_id == "s1"
	assert req.is_blocked is True


def test_update_show_not_found(shows_client_host):
	client, show_svc, _ = shows_client_host
	show_svc.not_found_ids.add("missing")

	resp = client.patch("/shows/missing", json={"is_blocked": False})

	assert resp.status_code == 404
	assert "show missing not found" in resp.text
	assert show_svc.update_calls == []
