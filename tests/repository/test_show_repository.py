from unittest.mock import MagicMock
import pytest
from botocore.exceptions import ClientError

from app.repository.show_repository import ShowRepository
from models.shows import Show
from models.venue import Venue
from models.events import Event
from datetime import datetime, timezone


def make_table_mock():
	table = MagicMock()
	table.name = "shows"
	table.meta.client = MagicMock()
	return table


def sample_show():
	return Show(
		id="s1",
		venue_id="v1",
		event_id="e1",
		is_blocked=False,
		price=150.0,
		show_date="2025-01-01",
		show_time="18:00",
		booked_seats=["A1", "A2"],
	)


def sample_venue():
	return Venue(
		id="v1",
		name="Hall",
		host_id="h1",
		city="NYC",
		state="NY",
		is_blocked=False,
		is_seat_layout_required=True,
	)


def sample_event(blocked: bool = False):
	return Event(
		id="e1",
		name="Concert",
		description="Live",
		duration=120,
		category="music",
		is_blocked=blocked,
		artist_ids=["a1"],
		artist_names=["Alice"],
	)


def test_to_ddb_ttl_converts_to_timestamp():
	expected = int(datetime(2025, 1, 1, 12, 30, tzinfo=timezone.utc).timestamp())
	ts = ShowRepository._to_ddb_ttl("2025-01-01", "12:30", tz="UTC")

	assert isinstance(ts, int)
	assert ts == expected


def test_create_show_calls_transact_write_items():
	table = make_table_mock()
	repo = ShowRepository(table=table)
	show = sample_show()
	venue = sample_venue()
	event = sample_event()

	repo.create_show(show=show, venue=venue, event=event)

	table.meta.client.transact_write_items.assert_called_once()
	_, kwargs = table.meta.client.transact_write_items.call_args
	transact = kwargs["TransactItems"]
	assert len(transact) == 5
	show_put = transact[0]["Put"]["Item"]
	assert show_put["pk"] == f"SHOW#{show.id}"
	assert show_put["expires_at"] == ShowRepository._to_ddb_ttl(
		show.show_date, show.show_time
	)
	host_event = transact[4]["Put"]["Item"]
	assert host_event["pk"] == f"HOST#{venue.host_id}"


def test_create_show_raises_when_event_blocked():
	table = make_table_mock()
	repo = ShowRepository(table=table)
	event = sample_event(blocked=True)

	with pytest.raises(Exception):
		repo.create_show(show=sample_show(), venue=sample_venue(), event=event)

	table.meta.client.transact_write_items.assert_not_called()


def test_get_show_by_id_returns_show():
	table = make_table_mock()
	table.get_item.return_value = {
		"Item": {
			"pk": "SHOW#s1",
			"sk": "DETAILS",
			"venue_id": "v1",
			"event_id": "e1",
			"is_show_blocked": False,
			"price": 150.0,
			"show_date": "2025-01-01",
			"show_time": "18:00",
			"booked_seats": ["A1"],
		}
	}
	repo = ShowRepository(table=table)

	show = repo.get_show_by_id("s1")

	assert isinstance(show, Show)
	assert show.id == "s1"
	assert show.venue_id == "v1"
	table.get_item.assert_called_once_with(Key={"pk": "SHOW#s1", "sk": "DETAILS"})


def test_get_show_by_id_missing_returns_none():
	table = make_table_mock()
	table.get_item.return_value = {}
	repo = ShowRepository(table=table)

	assert repo.get_show_by_id("missing") is None


def test_get_show_by_id_raises_client_error():
	table = make_table_mock()
	error = ClientError({"Error": {"Code": "Boom", "Message": "fail"}}, "GetItem")
	table.get_item.side_effect = error
	repo = ShowRepository(table=table)

	with pytest.raises(ClientError):
		repo.get_show_by_id("s1")


def test_batch_get_shows_by_ids_returns_shows():
	table = make_table_mock()
	table.meta.client.batch_get_item.return_value = {
		"Responses": {
			table.name: [
				{
					"pk": "SHOW#s1",
					"sk": "DETAILS",
					"venue_id": "v1",
					"event_id": "e1",
					"is_show_blocked": False,
					"price": 150.0,
					"show_date": "2025-01-01",
					"show_time": "18:00",
					"booked_seats": [],
				},
				{
					"pk": "SHOW#s2",
					"sk": "DETAILS",
					"venue_id": "v2",
					"event_id": "e2",
					"is_show_blocked": True,
					"price": 200.0,
					"show_date": "2025-01-02",
					"show_time": "20:00",
					"booked_seats": ["B1"],
				},
			]
		}
	}
	repo = ShowRepository(table=table)

	shows = repo.batch_get_shows_by_ids(["s1", "s2"])

	assert {s.id for s in shows} == {"s1", "s2"}
	expected_keys = [
		{"pk": "SHOW#s1", "sk": "DETAILS"},
		{"pk": "SHOW#s2", "sk": "DETAILS"},
	]
	table.meta.client.batch_get_item.assert_called_once_with(
		RequestItems={table.name: {"Keys": expected_keys}}
	)


def test_batch_get_shows_by_ids_raises_client_error():
	table = make_table_mock()
	error = ClientError({"Error": {"Code": "Boom", "Message": "fail"}}, "BatchGetItem")
	table.meta.client.batch_get_item.side_effect = error
	repo = ShowRepository(table=table)

	with pytest.raises(ClientError):
		repo.batch_get_shows_by_ids(["s1"])


def test_list_by_event_city_returns_shows():
	table = make_table_mock()
	table.query.return_value = {
		"Items": [
			{"pk": "EVENT#e1#CITY#NYC", "sk": "VENUE#v1#SHOW#s1"},
			{"pk": "EVENT#e1#CITY#NYC", "sk": "VENUE#v2#SHOW#s2"},
		]
	}
	repo = ShowRepository(table=table)
	repo.batch_get_shows_by_ids = MagicMock(return_value=[sample_show(), sample_show()])

	shows = repo.list_by_event_city(event_id="e1", city="NYC")

	assert len(shows) == 2
	repo.batch_get_shows_by_ids.assert_called_once_with(show_ids=["s1", "s2"])
	table.query.assert_called_once()


def test_list_by_event_city_empty_returns_empty_list():
	table = make_table_mock()
	table.query.return_value = {"Items": []}
	repo = ShowRepository(table=table)
	repo.batch_get_shows_by_ids = MagicMock()

	shows = repo.list_by_event_city(event_id="e1", city="NYC")

	assert shows == []
	repo.batch_get_shows_by_ids.assert_not_called()
	table.query.assert_called_once()


def test_list_by_event_city_raises_client_error():
	table = make_table_mock()
	error = ClientError({"Error": {"Code": "Boom", "Message": "fail"}}, "Query")
	table.query.side_effect = error
	repo = ShowRepository(table=table)

	with pytest.raises(ClientError):
		repo.list_by_event_city(event_id="e1", city="NYC")


def test_list_by_event_date_returns_shows_skipping_blocked():
	table = make_table_mock()
	table.query.return_value = {
		"Items": [
			{
				"pk": "EVENT#e1#CITY#NYC",
				"sk": "DATE#2025-01-01#VENUE#v1#SHOW#s1",
				"is_show_blocked": False,
				"is_event_blocked": False,
				"price": 150.0,
				"booked_seats": ["A1"],
				"show_date": "2025-01-01",
				"show_time": "18:00",
			},
			{
				"pk": "EVENT#e1#CITY#NYC",
				"sk": "DATE#2025-01-01#VENUE#v1#SHOW#s2",
				"is_show_blocked": True,
				"is_event_blocked": False,
				"price": 200.0,
				"booked_seats": ["B1"],
				"show_date": "2025-01-01",
				"show_time": "20:00",
			},
		]
	}
	repo = ShowRepository(table=table)

	shows = repo.list_by_event_date(event_id="e1", city="NYC", date="2025-01-01")

	assert len(shows) == 1
	assert shows[0].id == "s1"
	table.query.assert_called_once()


def test_list_by_event_date_returns_empty_when_event_blocked():
	table = make_table_mock()
	table.query.return_value = {
		"Items": [
			{
				"pk": "EVENT#e1#CITY#NYC",
				"sk": "DATE#2025-01-01#VENUE#v1#SHOW#s1",
				"is_event_blocked": True,
			}
		]
	}
	repo = ShowRepository(table=table)

	shows = repo.list_by_event_date(event_id="e1", city="NYC", date="2025-01-01")

	assert shows == []
	table.query.assert_called_once()


def test_list_by_event_date_returns_none_on_no_items():
	table = make_table_mock()
	table.query.return_value = {"Items": []}
	repo = ShowRepository(table=table)

	assert repo.list_by_event_date(event_id="e1", city="NYC", date="2025-01-01") is None
	table.query.assert_called_once()


def test_list_by_event_date_raises_client_error():
	table = make_table_mock()
	error = ClientError({"Error": {"Code": "Boom", "Message": "fail"}}, "Query")
	table.query.side_effect = error
	repo = ShowRepository(table=table)

	with pytest.raises(ClientError):
		repo.list_by_event_date(event_id="e1", city="NYC", date="2025-01-01")


def test_update_show_calls_transact_write_items():
	table = make_table_mock()
	repo = ShowRepository(table=table)
	venue = sample_venue()
	show = sample_show()

	repo.update_show(show_id="s1", is_blocked=True, venue=venue, show=show)

	table.meta.client.transact_write_items.assert_called_once()
	_, kwargs = table.meta.client.transact_write_items.call_args
	transact = kwargs["TransactItems"]
	assert len(transact) == 2
	first_update = transact[0]["Update"]
	assert first_update["Key"] == {"pk": "SHOW#s1", "sk": "DETAILS"}
	assert first_update["ExpressionAttributeValues"] == {":new_value": True}
	second_update = transact[1]["Update"]
	assert second_update["Key"]["pk"] == f"EVENT#{show.event_id}#CITY#{venue.city}"
	assert second_update["ConditionExpression"] == "attribute_exists(pk)"


def test_update_show_raises_client_error():
	table = make_table_mock()
	error = ClientError({"Error": {"Code": "Boom", "Message": "fail"}}, "TransactWriteItems")
	table.meta.client.transact_write_items.side_effect = error
	repo = ShowRepository(table=table)

	with pytest.raises(ClientError):
		repo.update_show(show_id="s1", is_blocked=False, venue=sample_venue(), show=sample_show())


def test_create_show_raises_client_error_on_write_failure():
	table = make_table_mock()
	error = ClientError({"Error": {"Code": "Boom", "Message": "fail"}}, "TransactWriteItems")
	table.meta.client.transact_write_items.side_effect = error
	repo = ShowRepository(table=table)

	with pytest.raises(ClientError):
		repo.create_show(show=sample_show(), venue=sample_venue(), event=sample_event())

