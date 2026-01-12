import pytest

from conftest import venues_client_admin, venues_client_host


def test_add_venue_host_calls_service(venues_client_host):
	client, venue_svc, user = venues_client_host
	payload = {
		"name": "Hall",
		"city": "NYC",
		"state": "NY",
		"is_seat_layout_required": True,
	}

	resp = client.post("/venues", json=payload)

	assert resp.status_code == 201
	body = resp.json()
	assert body["message"] == "added venue successfully"
	assert body["data"] == venue_svc.venue_return
	assert len(venue_svc.add_calls) == 1
	req_obj, host_id = venue_svc.add_calls[0]
	assert host_id == user["user_id"]
	assert req_obj.name == "Hall"


def test_get_venue_by_id_calls_service(venues_client_admin):
	client, venue_svc, _ = venues_client_admin

	resp = client.get("/venues/v1")

	assert resp.status_code == 200
	assert venue_svc.get_calls == ["v1"]


def test_update_venue_calls_service(venues_client_host):
	client, venue_svc, user = venues_client_host

	resp = client.patch("/venues/v1", json={"is_blocked": True})

	assert resp.status_code == 200
	assert venue_svc.update_calls == [("v1", user["user_id"], True)]
	assert resp.json()["message"] == "successfully updated v1"


def test_delete_venue_calls_service(venues_client_host):
	client, venue_svc, user = venues_client_host

	resp = client.delete("/venues/v1")

	assert resp.status_code == 200
	assert venue_svc.delete_calls == [("v1", user["user_id"])]
	assert resp.json()["message"] == "successfully deleted v1"


def test_get_venue_not_found_uses_handler(venues_client_admin):
	client, venue_svc, _ = venues_client_admin
	venue_svc.not_found_ids.add("missing")

	resp = client.get("/venues/missing")

	assert resp.status_code == 404
	assert "venue missing not found" in resp.text
	assert venue_svc.get_calls == ["missing"]


def test_update_venue_not_found(venues_client_host):
	client, venue_svc, _ = venues_client_host
	venue_svc.not_found_ids.add("missing")

	resp = client.patch("/venues/missing", json={"is_blocked": True})

	assert resp.status_code == 404
	assert "venue missing not found" in resp.text
	assert venue_svc.update_calls == []


def test_delete_venue_client_error(venues_client_host):
	client, venue_svc, _ = venues_client_host
	venue_svc.client_error_ids.add("v1")

	resp = client.delete("/venues/v1")

	assert resp.status_code == 500
	assert "delete failed" in resp.text
	assert venue_svc.delete_calls == []
