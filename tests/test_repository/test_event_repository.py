from unittest.mock import MagicMock
import pytest
from botocore.exceptions import ClientError

from app.repository.event_repository import EventRepository
from app.models.events import Event


def make_table_mock():
	table = MagicMock()
	table.name = "events"
	table.meta.client = MagicMock()
	return table


def sample_event():
	return Event(
		id="e1",
		name="Concert",
		description="Live music",
		duration=120,
		category="music",
		is_blocked=False,
		artist_ids=["a1", "a2"],
		artist_names=["Alice", "Bob"],
	)


def test_add_event_calls_transact_write_items():
	table = make_table_mock()
	repo = EventRepository(table=table)
	event = sample_event()

	repo.add_event(event)

	table.meta.client.transact_write_items.assert_called_once()
	_, kwargs = table.meta.client.transact_write_items.call_args
	transact = kwargs["TransactItems"]
	assert len(transact) == 2
	first_put = transact[0]["Put"]
	second_put = transact[1]["Put"]
	assert first_put["Item"]["pk"] == f"EVENT#{event.id}"
	assert first_put["ConditionExpression"] == "attribute_not_exists(pk)"
	assert second_put["Item"]["pk"] == "EVENTS"


def test_add_event_raises_on_client_error():
	table = make_table_mock()
	error = ClientError({"Error": {"Code": "Boom", "Message": "fail"}}, "TransactWriteItems")
	table.meta.client.transact_write_items.side_effect = error
	repo = EventRepository(table=table)

	with pytest.raises(ClientError):
		repo.add_event(sample_event())


def test_get_by_id_returns_event():
	table = make_table_mock()
	table.get_item.return_value = {
		"Item": {
			"pk": "EVENT#e1",
			"sk": "DETAILS",
			"event_name": "Concert",
			"description": "Live music",
			"duration": 120,
			"category": "music",
			"is_event_blocked": False,
			"artist_ids": ["a1"],
			"artist_names": ["Alice"],
		}
	}
	repo = EventRepository(table=table)

	event = repo.get_by_id("e1")

	assert isinstance(event, Event)
	assert event.id == "e1"
	assert event.name == "Concert"
	assert event.artist_ids == ["a1"]
	table.get_item.assert_called_once_with(Key={"pk": "EVENT#e1", "sk": "DETAILS"})


def test_get_by_id_missing_returns_none():
	table = make_table_mock()
	table.get_item.return_value = {}
	repo = EventRepository(table=table)

	assert repo.get_by_id("missing") is None


def test_get_by_id_raises_client_error():
	table = make_table_mock()
	error = ClientError({"Error": {"Code": "Boom", "Message": "fail"}}, "GetItem")
	table.get_item.side_effect = error
	repo = EventRepository(table=table)

	with pytest.raises(ClientError):
		repo.get_by_id("e1")


def test_get_events_by_name_returns_events():
	table = make_table_mock()
	table.query.return_value = {
		"Items": [
			{
				"pk": "EVENTS",
				"sk": "EVENT_NAME#Concert#EVENT_ID#e1",
				"description": "Live music",
				"duration": 120,
				"category": "music",
				"is_event_blocked": False,
				"artist_ids": ["a1"],
				"artist_names": ["Alice"],
			}
		]
	}
	repo = EventRepository(table=table)
	repo._batch_get_events = MagicMock(return_value=[sample_event()])

	events = repo.get_events_by_name("Concert")

	assert len(events) == 1
	repo._batch_get_events.assert_called_once_with(event_ids=["e1"])
	table.query.assert_called_once()


def test_get_events_by_name_empty_returns_empty_list():
	table = make_table_mock()
	table.query.return_value = {"Items": []}
	repo = EventRepository(table=table)
	repo._batch_get_events = MagicMock(return_value=[])

	assert repo.get_events_by_name("Missing") == []
	repo._batch_get_events.assert_called_once_with(event_ids=[])
	table.query.assert_called_once()


def test_get_events_of_host_returns_events():
	table = make_table_mock()
	table.query.return_value = {
		"Items": [
			{"pk": "HOST#h1", "sk": "EVENT#e1"},
			{"pk": "HOST#h1", "sk": "EVENT#e2"},
		]
	}
	repo = EventRepository(table=table)
	repo._batch_get_events = MagicMock(
		return_value=[sample_event(), sample_event()]
	)

	events = repo.get_events_of_host("h1")

	assert len(events) == 2
	repo._batch_get_events.assert_called_once_with(event_ids=["e1", "e2"])
	table.query.assert_called_once()


def test_get_events_of_host_empty_returns_empty_list():
	table = make_table_mock()
	table.query.return_value = {"Items": []}
	repo = EventRepository(table=table)
	repo._batch_get_events = MagicMock()

	events = repo.get_events_of_host("h1")

	assert events == []
	repo._batch_get_events.assert_not_called()
	table.query.assert_called_once()


def test_batch_get_events_handles_unprocessed_keys():
	table = make_table_mock()
	first_resp = {
		"Responses": {
			table.name: [
				{
					"pk": "EVENT#e1",
					"sk": "DETAILS",
					"event_name": "Concert",
					"description": "Live music",
					"duration": 120,
					"category": "music",
					"is_event_blocked": False,
					"artist_ids": ["a1"],
					"artist_names": ["Alice"],
				}
			]
		},
		"UnprocessedKeys": {table.name: {"Keys": [{"pk": "EVENT#e2", "sk": "DETAILS"}]}}
	}
	second_resp = {
		"Responses": {
			table.name: [
				{
					"pk": "EVENT#e2",
					"sk": "DETAILS",
					"event_name": "Workshop",
					"description": "Learn",
					"duration": 60,
					"category": "education",
					"is_event_blocked": True,
					"artist_ids": [],
					"artist_names": [],
				}
			]
		},
		"UnprocessedKeys": {},
	}
	table.meta.client.batch_get_item.side_effect = [first_resp, second_resp]
	repo = EventRepository(table=table)

	events = repo._batch_get_events(["e1", "e2"])

	assert {e.id for e in events} == {"e1", "e2"}
	assert table.meta.client.batch_get_item.call_count == 2


def test_get_events_by_city_and_name_returns_events():
	table = make_table_mock()
	table.query.return_value = {
		"Items": [
			{
				"pk": "CITY#NYC",
				"sk": "NAME#Concert#ID#e1",
				"description": "Live",
				"duration": 120,
				"category": "music",
				"is_event_blocked": False,
				"artist_ids": ["a1"],
				"artist_names": ["Alice"],
			}
		]
	}
	repo = EventRepository(table=table)
	repo._batch_get_events = MagicMock(return_value=[sample_event()])

	events = repo.get_events_by_city_and_name(city="NYC", name="Concert")

	assert len(events) == 1
	repo._batch_get_events.assert_called_once_with(event_ids=["e1"])
	table.query.assert_called_once()


def test_get_events_by_city_and_name_empty_returns_empty_list():
	table = make_table_mock()
	table.query.return_value = {"Items": []}
	repo = EventRepository(table=table)
	repo._batch_get_events = MagicMock()

	events = repo.get_events_by_city_and_name(city="NYC", name="Missing")

	assert events == []
	repo._batch_get_events.assert_not_called()
	table.query.assert_called_once()


def test_batch_get_events_empty_list_returns_empty_and_skips_client_call():
	table = make_table_mock()
	repo = EventRepository(table=table)

	result = repo._batch_get_events([])

	assert result == []
	table.meta.client.batch_get_item.assert_not_called()


def test_update_event_calls_transact_write_items():
	table = make_table_mock()
	repo = EventRepository(table=table)

	repo.update_event(event_id="e1", is_blocked=True)

	table.meta.client.transact_write_items.assert_called_once()
	_, kwargs = table.meta.client.transact_write_items.call_args
	transact = kwargs["TransactItems"]
	assert len(transact) == 1
	update = transact[0]["Update"]
	assert update["Key"] == {"pk": "EVENT#e1", "sk": "DETAILS"}
	assert update["ExpressionAttributeValues"] == {":new_value": True}
	assert update["ConditionExpression"] == "attribute_exists(pk)"


def test_update_event_raises_client_error():
	table = make_table_mock()
	error = ClientError({"Error": {"Code": "Boom", "Message": "fail"}}, "TransactWriteItems")
	table.meta.client.transact_write_items.side_effect = error
	repo = EventRepository(table=table)

	with pytest.raises(ClientError):
		repo.update_event(event_id="e1", is_blocked=False)

