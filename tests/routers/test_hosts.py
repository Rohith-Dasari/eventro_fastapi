import pytest

from conftest import hosts_client_admin, hosts_client_host_mismatch


def test_get_host_venues_admin_allowed(hosts_client_admin):
	client, venue_svc, _ = hosts_client_admin

	resp = client.get("/hosts/h1/venues")

	assert resp.status_code == 200
	body = resp.json()
	assert body["message"] == "successfully retrieved h1's venues"
	assert body["data"] == venue_svc.return_value
	assert venue_svc.host_calls == [("h1", None)]


def test_get_host_venues_admin_with_is_blocked_query(hosts_client_admin):
	client, venue_svc, _ = hosts_client_admin

	resp = client.get("/hosts/h1/venues", params={"is_blocked": True})

	assert resp.status_code == 200
	assert venue_svc.host_calls == [("h1", True)]


def test_get_host_venues_forbidden_for_other_host(hosts_client_host_mismatch):
	client, _, _ = hosts_client_host_mismatch

	resp = client.get("/hosts/h1/venues")

	assert resp.status_code == 401
	assert "not authorised" in resp.text


def test_get_host_events_admin_allowed(hosts_client_admin):
	client, _, event_svc = hosts_client_admin

	resp = client.get("/hosts/h1/events")

	assert resp.status_code == 200
	body = resp.json()
	assert body["message"] == "successfully retrieved h1's events"
	assert body["data"] == event_svc.return_value
	assert event_svc.host_calls == ["h1"]


def test_get_host_events_forbidden_for_other_host(hosts_client_host_mismatch):
	client, _, _ = hosts_client_host_mismatch

	resp = client.get("/hosts/h1/events")

	assert resp.status_code == 401
	assert "not authorised" in resp.text
