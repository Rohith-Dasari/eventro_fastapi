from unittest.mock import MagicMock
import pytest
from botocore.exceptions import ClientError

from app.repository.venue_repository import VenueRepository
from app.models.venue import Venue


def make_table_mock():
	table = MagicMock()
	table.name = "venues"
	table.meta.client = MagicMock()
	return table


def sample_venue():
	return Venue(
		id="v1",
		name="Venue",
		host_id="h1",
		city="c",
		state="s",
		is_blocked=False,
		is_seat_layout_required=True,
	)


def test_add_venue_calls_transact_write_items():
	table = make_table_mock()
	repo = VenueRepository(table=table)
	venue = sample_venue()

	repo.add_venue(venue)

	table.meta.client.transact_write_items.assert_called_once()
	items = table.meta.client.transact_write_items.call_args.kwargs["TransactItems"]
	assert len(items) == 2
	assert items[0]["Put"]["Item"]["pk"] == f"USER#{venue.host_id}"
	assert items[1]["Put"]["Item"]["pk"] == f"VENUE#{venue.id}"


def test_add_venue_raises_on_client_error():
	table = make_table_mock()
	error = ClientError({"Error": {"Code": "X", "Message": "fail"}}, "TransactWriteItems")
	table.meta.client.transact_write_items.side_effect = error
	repo = VenueRepository(table=table)

	with pytest.raises(ClientError):
		repo.add_venue(sample_venue())


def test_get_venue_by_id_found():
	table = make_table_mock()
	table.get_item.return_value = {
		"Item": {
			"pk": "VENUE#v1",
			"sk": "DETAILS",
			"venue_name": "V",
			"host_id": "h1",
			"venue_city": "c",
			"venue_state": "s",
			"is_venue_blocked": False,
			"is_seat_layout_required": True,
		}
	}
	repo = VenueRepository(table=table)

	venue = repo.get_venue_by_id("v1")

	assert venue.id == "v1"
	assert venue.name == "V"
	assert venue.host_id == "h1"
	assert venue.city == "c"
	table.get_item.assert_called_once_with(Key={"pk": "VENUE#v1", "sk": "DETAILS"})


def test_get_venue_by_id_missing_returns_none():
	table = make_table_mock()
	table.get_item.return_value = {}
	repo = VenueRepository(table=table)

	assert repo.get_venue_by_id("missing") is None


def test_get_host_venues_happy_path():
	table = make_table_mock()
	table.query.return_value = {
		"Items": [
			{
				"pk": "USER#h1",
				"sk": "VENUE#v1",
				"venue_name": "V1",
				"venue_city": "c",
				"venue_state": "s",
				"is_venue_blocked": False,
				"is_seat_layout_required": True,
			},
			{
				"pk": "USER#h1",
				"sk": "VENUE#v2",
				"venue_name": "V2",
				"venue_city": "c",
				"venue_state": "s",
				"is_venue_blocked": True,
				"is_seat_layout_required": False,
			},
		]
	}
	repo = VenueRepository(table=table)

	venues = repo.get_host_venues(host_id="h1")

	assert len(venues) == 2
	assert venues[0].id == "v1"
	assert venues[1].id == "v2"
	table.query.assert_called_once()


def test_get_host_venues_client_error_propagates():
	table = make_table_mock()
	error = ClientError({"Error": {"Code": "X", "Message": "fail"}}, "Query")
	table.query.side_effect = error
	repo = VenueRepository(table=table)

	with pytest.raises(ClientError):
		repo.get_host_venues(host_id="h1")


def test_update_venue_calls_transact_write_items():
	table = make_table_mock()
	repo = VenueRepository(table=table)

	repo.update_venue(venue_id="v1", host_id="h1", is_blocked=True)

	table.meta.client.transact_write_items.assert_called_once()
	calls = table.meta.client.transact_write_items.call_args.kwargs["TransactItems"]
	assert len(calls) == 2
	assert calls[0]["Update"]["Key"] == {"pk": "VENUE#v1", "sk": "DETAILS"}
	assert calls[1]["Update"]["Key"] == {"pk": "USER#h1", "sk": "VENUE#v1"}


def test_update_venue_propagates_client_error():
	table = make_table_mock()
	error = ClientError({"Error": {"Code": "X", "Message": "fail"}}, "TransactWriteItems")
	table.meta.client.transact_write_items.side_effect = error
	repo = VenueRepository(table=table)

	with pytest.raises(ClientError):
		repo.update_venue(venue_id="v1", host_id="h1", is_blocked=True)


def test_delete_venue_calls_transact_write_items():
	table = make_table_mock()
	repo = VenueRepository(table=table)

	repo.delete_venue(venue_id="v1", host_id="h1")

	table.meta.client.transact_write_items.assert_called_once()
	calls = table.meta.client.transact_write_items.call_args.kwargs["TransactItems"]
	assert len(calls) == 2
	assert calls[0]["Delete"]["Key"] == {"pk": "VENUE#v1", "sk": "DETAILS"}
	assert calls[1]["Delete"]["Key"] == {"pk": "USER#h1", "sk": "VENUE#v1"}
	assert calls[1]["Delete"]["ConditionExpression"] == "attribute_exists(pk)"


def test_delete_venue_propagates_client_error():
	table = make_table_mock()
	error = ClientError({"Error": {"Code": "X", "Message": "fail"}}, "TransactWriteItems")
	table.meta.client.transact_write_items.side_effect = error
	repo = VenueRepository(table=table)

	with pytest.raises(ClientError):
		repo.delete_venue(venue_id="v1", host_id="h1")


def test_batch_get_venues_returns_list():
	table = make_table_mock()
	table.meta.client.batch_get_item.return_value = {
		"Responses": {
			table.name: [
				{
					"pk": "VENUE#v1",
					"sk": "DETAILS",
					"venue_name": "V1",
					"host_id": "h1",
					"venue_city": "c",
					"venue_state": "s",
					"is_venue_blocked": False,
					"is_seat_layout_required": True,
				}
			]
		}
	}
	repo = VenueRepository(table=table)

	venues = repo.batch_get_venues(["v1"])

	assert len(venues) == 1
	assert venues[0].id == "v1"
	table.meta.client.batch_get_item.assert_called_once()


def test_batch_get_venues_empty_input_returns_empty_and_no_call():
	table = make_table_mock()
	repo = VenueRepository(table=table)

	venues = repo.batch_get_venues([])

	assert venues == []
	table.meta.client.batch_get_item.assert_not_called()
