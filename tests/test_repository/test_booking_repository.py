from unittest.mock import MagicMock
import pytest
from botocore.exceptions import ClientError

from app.repository.booking_repository import BookingRepository
from app.models.booking import Booking
from app.models.shows import Show
from app.models.events import Event
from app.models.venue import Venue
from app.schemas.booking import BookingResponse


def make_table_mock():
    table = MagicMock()
    table.name = "bookings"
    table.meta.client = MagicMock()
    return table


def sample_booking():
    return Booking(
        booking_id="b1",
        user_id="u1",
        show_id="s1",
        time_booked="2025-01-01T10:00:00Z",
        total_booking_price="300",
        seats=["A1", "A2"],
    )


def sample_show():
    return Show(
        id="s1",
        venue_id="v1",
        event_id="e1",
        is_blocked=False,
        price=150.0,
        show_date="2025-01-05",
        show_time="18:00",
        booked_seats=["B1"],
    )


def sample_event():
    return Event(
        id="e1",
        name="Concert",
        description="Live",
        duration=120,
        category="music",
        is_blocked=False,
        artist_ids=["a1"],
        artist_names=["Alice"],
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


def test_add_booking_calls_transact_write_items():
    table = make_table_mock()
    repo = BookingRepository(table=table)
    booking = sample_booking()
    show = sample_show()
    event = sample_event()
    venue = sample_venue()

    repo.add_booking(booking=booking, show=show, event=event, venue=venue)

    table.meta.client.transact_write_items.assert_called_once()
    _, kwargs = table.meta.client.transact_write_items.call_args
    transact = kwargs["TransactItems"]
    assert len(transact) == 2
    update = transact[0]["Update"]
    assert update["Key"] == {"pk": f"SHOW#{show.id}", "sk": "DETAILS"}
    assert update["ExpressionAttributeValues"] == {
        ":empty_list": [],
        ":vals": booking.seats,
    }
    put_item = transact[1]["Put"]["Item"]
    assert put_item["pk"] == f"USER#{booking.user_id}"
    assert put_item["sk"].startswith("SHOW_DATE#")
    assert put_item["event_id"] == event.id
    assert put_item["venue_id"] == venue.id


def test_add_booking_raises_client_error():
    table = make_table_mock()
    error = ClientError(
        {"Error": {"Code": "Boom", "Message": "fail"}}, "TransactWriteItems"
    )
    table.meta.client.transact_write_items.side_effect = error
    repo = BookingRepository(table=table)

    with pytest.raises(ClientError):
        repo.add_booking(
            sample_booking(), sample_show(), sample_event(), sample_venue()
        )


def test_get_bookings_returns_responses():
    table = make_table_mock()
    table.query.return_value = {
        "Items": [
            {
                "pk": "USER#u1",
                "sk": "SHOW_DATE#2025-01-05#BOOKING#b1",
                "show_id": "s1",
                "time_booked": "2025-01-01T10:00:00Z",
                "total_price": 300,
                "seats": ["A1", "A2"],
                "venue_city": "NYC",
                "venue_name": "Hall",
                "venue_state": "NY",
                "event_name": "Concert",
                "event_duration": 120,
                "event_id": "e1",
            }
        ]
    }
    repo = BookingRepository(table=table)

    results = repo.get_bookings(user_id="u1")

    assert len(results) == 1
    assert isinstance(results[0], BookingResponse)
    assert results[0].booking_id == "b1"
    assert results[0].booking_date == "2025-01-05"
    assert results[0].total_price == 300
    table.query.assert_called_once()


def test_get_bookings_empty_returns_empty_list():
    table = make_table_mock()
    table.query.return_value = {"Items": []}
    repo = BookingRepository(table=table)

    assert repo.get_bookings(user_id="u1") == []
    table.query.assert_called_once()


def test_get_bookings_raises_client_error():
    table = make_table_mock()
    error = ClientError({"Error": {"Code": "Boom", "Message": "fail"}}, "Query")
    table.query.side_effect = error
    repo = BookingRepository(table=table)

    with pytest.raises(ClientError):
        repo.get_bookings(user_id="u1")
