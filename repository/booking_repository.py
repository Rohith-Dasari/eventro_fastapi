from botocore.exceptions import ClientError
import logging
from types_boto3_dynamodb.service_resource import Table
from types_boto3_dynamodb import DynamoDBClient
from typing import Optional, List
from boto3.dynamodb.conditions import Key
from models.booking import Booking
from schemas.shows import ShowResponse
from models.events import Event


class BookingRepository:
    def __init__(self, table: Table, Client: DynamoDBClient = None):
        self.table = table
        self.client = table.meta.client

    def add_booking(
        self, booking: Booking, user_id: str, show: ShowResponse, event: Event
    ):
        booking_item = {
            "pk": f"USER#{user_id}",
            "sk": f"SHOW_DATE#{show.show_date}#BOOKING#{booking.booking_id}",
            "show_id": show.id,
            "time_booked": booking.time_booked,
            "total_price": booking.total_booking_price,
            "seats": booking.seats,
            "venue_city": show.venue["city"],
            "venue_id": show.venue["name"],
            "venue_state": show.venue["state"],
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

    def get_bookings(self, user_id: str) -> List[Booking]:
        try:
            response = self.table.query(
                KeyConditionExpression=(
                    Key("pk").eq(f"USER{user_id}") & Key("sk").begins_with("SHOW_DATE#")
                )
            )
            items = response.get("Items", [])
            if not items:
                return None

            bookings: List[Booking] = []
            for item in items:
                booking = Booking(
                    booking_id=item["sk"].split("#BOOKING#")[-1],
                    user_id=item["pk"].removeprefix("USER#"),
                    show_id=item["show_id"],
                    time_booked=item["time_booked"],
                    total_booking_price=item["total_price"],
                    seats=item["seats"],
                )
                bookings.append(booking)
            return bookings

        except ClientError as err:
            raise
