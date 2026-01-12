from botocore.exceptions import ClientError
import logging
from types_boto3_dynamodb.service_resource import Table
from types_boto3_dynamodb import DynamoDBClient
from typing import Optional, List
from boto3.dynamodb.conditions import Key
from models.booking import Booking
from models.shows import Show
from models.events import Event
from models.venue import Venue
from schemas.booking import BookingResponse


class BookingRepository:
    def __init__(self, table: Table, client: DynamoDBClient = None):
        self.table = table
        self.client = table.meta.client

    def add_booking(
        self,
        booking: Booking,
        show: Show,
        event: Event,
        venue: Venue,
    ):
        booking_item = {
            "pk": f"USER#{booking.user_id}",
            "sk": f"SHOW_DATE#{show.show_date}#BOOKING#{booking.booking_id}",
            "show_id": show.id,
            "time_booked": booking.time_booked,
            "total_price": booking.total_booking_price,
            "seats": booking.seats,
            "venue_city": venue.city,
            "venue_id": venue.id,
            "venue_name": venue.name,
            "venue_state": venue.state,
            "event_name": event.name,
            "event_duration": event.duration,
            "event_id": event.id,
        }
        try:
            self.client.transact_write_items(
                TransactItems=[
                    {
                        "Update": {
                            "TableName": self.table.name,
                            "Key": {"pk": f"SHOW#{show.id}", "sk": f"DETAILS"},
                            "UpdateExpression": f"SET #l = list_append(if_not_exists(#l, :empty_list), :vals)",
                            "ExpressionAttributeNames": {"#l": "booked_seats"},
                            "ExpressionAttributeValues": {
                                ":empty_list": [],
                                ":vals": booking.seats,
                            },
                        }
                    },
                    {
                        "Put": {
                            "TableName": self.table.name,
                            "Item": booking_item,
                        }
                    },
                ]
            )
        except ClientError as e:
            raise

    def get_bookings(self, user_id: str) -> List[BookingResponse]:
        try:
            response = self.table.query(
                KeyConditionExpression=(
                    Key("pk").eq(f"USER#{user_id}") & Key("sk").begins_with("SHOW_DATE#")
                )
            )
            items = response.get("Items", [])
            if not items:
                return []

            bookings: List[BookingResponse] = []
            for item in items:
                booking = BookingResponse(
                    booking_id=item["sk"].split("#BOOKING#")[-1],
                    user_id=user_id,
                    show_id=item["show_id"],
                    time_booked=item["time_booked"],
                    total_price=item["total_price"],
                    seats=item["seats"],
                    venue_city=item["venue_city"],
                    venue_name=item["venue_name"],
                    venue_state=item["venue_state"],
                    event_name=item["event_name"],
                    event_duration=item["event_duration"],
                    event_id=item["event_id"],
                    booking_date=item["sk"]
                    .split("#BOOKING#")[0]
                    .removeprefix("SHOW_DATE#"),
                )
                bookings.append(booking)
            return bookings

        except ClientError as err:
            raise
