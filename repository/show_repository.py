from types_boto3_dynamodb.service_resource import Table
from types_boto3_dynamodb import DynamoDBClient
from botocore.exceptions import ClientError
from models.shows import Show
from models.venue import Venue
from models.events import Event
import logging
from boto3.dynamodb.conditions import Key
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)
from zoneinfo import ZoneInfo


# create
# get show by id
# list by event
# update


# todo:
# update show booking booking chesinappudu
class ShowRepository:
    def __init__(self, table: Table, client: DynamoDBClient = None):
        self.table = table
        self.client = client if client else table.meta.client

    def _to_ddb_ttl(date_str: str, time_str: str, tz="Asia/Kolkata") -> int:
        dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M").replace(
            tzinfo=ZoneInfo(tz)
        )

        return int(dt.timestamp())

    def create_show(self, show: Show, venue: Venue, event: Event):
        if event.is_blocked:
            raise Exception("cant add show to blocked event")

        ttl = self._to_ddb_ttl(show.date, show.show_time)
        show_item = {
            "pk": f"SHOW#{show.id}",
            "sk": f"DETAILS",
            "venue_city": venue.city,
            "venue_id": venue.id,
            "event_id": show.event_id,
            "price": show.price,
            "show_date": show.show_date,
            "show_time": show.show_time,
            "booked_seats": [],
            "is_show_blocked": False,
            "expires_at": ttl,
        }
        host_event = {
            "pk": f"HOST#{venue.host_id}",
            "sk": f"EVENT#{show.event_id}",
            "expires_at": ttl,
        }
        city_event = {
            "pk": f"CITY#{venue.city}",
            "sk": f"EVENT#{event.id}",
            "event_name": event.name,
            "description": event.description,
            "duration": event.duration,
            "category": event.category,
            "is_event_blocked": event.is_blocked,
            "artist_ids": event.artist_ids,
            "expires_at": ttl,
        }
        event_shows = {
            "pk": f"EVENT#{event.id}#CITY#{venue.city}",
            "sk": f"DATE#{show.show_date}#VENUE#{venue.id}#SHOW{show.id}",
            "is_event_blocked": show.is_blocked,
            "price": show.price,
            "is_show_blocked": False,
            "show_time": show.show_time,
            "booked_seats": [],
            "expires_at": ttl,
        }

        try:
            self.client.transact_write_items(
                TransactItems=[
                    {
                        "Put": {
                            "TableName": self.table.name,
                            "Item": show_item,
                        },
                        "Put": {
                            "TableName": self.table.name,
                            "Item": event_shows,
                        },
                        "Put": {
                            "TableName": self.table.name,
                            "Item": city_event,
                        },
                        "Put": {
                            "TableName": self.table.name,
                            "Item": host_event,
                        },
                    }
                ]
            )
        except ClientError as e:
            raise

    def get_show_by_id(self, show_id: str) -> Optional[Show]:
        try:
            response = self.table.get_item(
                Key={"pk": f"SHOW{show_id}", "sk": "DETAILS"}
            )
        except ClientError as err:
            logger.error(f"Error retrieving show by id {show_id}: {err}")
            raise
        item = response.get("Item", [])
        if not item:
            return None

        return Show(
            id=item["pk"].split("#", 1)[1],
            host_id=item["host_id"],
            venue_id=item["venue_id"],
            event_id=item["venue"],
            is_blocked=item["is_show_blocked"],
            price=item["price"],
            show_date=item["show_date"],
            show_time=item["show_time"],
            booked_seats=item["booked_seats"],
        )

    def list_by_event(self, event_id: str, city: str, date: str) -> List[Show]:
        try:
            response = self.table.query(
                KeyConditionExpression=(
                    Key("pk").eq(f"EVENT#{event_id}#CITY#{city}")
                    & Key("sk").begins_with(f"DATE{date}")
                )
            )
        except ClientError as err:
            logger.error(f"Error retrieving event: {event_id} shows: {err}")
            raise

        items = response.get("Items", [])
        if not items:
            return None

        shows: List[Show] = []
        if items[0].get("is_event_blocked"):
            return []

        for item in items:
            show = Show(
                id=item["sk"].split("SHOW#", 1)[1],
                venue_id=item["sk"].split("#")[3],
                event_id=event_id,
                is_blocked=item["is_show_blocked"],
                price=item["price"],
                booked_seats=item["booked_seats"],
                show_date=item["show_date"],
                show_time=item["show_time"],
            )
            if show.is_blocked:
                continue
            shows.append(show)
        return shows

    def update_show(self, show_id: str, is_blocked, venue: Venue, show: Show):

        try:
            self.client.transact_write_items(
                TransactItems=[
                    {
                        "Update": {
                            "Key": {"pk": f"SHOW#{show_id}", "sk": "DETAILS"},
                            "TableName": self.table.name,
                            "UpdateExpression": "SET #is_blocked=:new_value",
                            "ExpressionAttributeNames": {
                                "#is_blocked": "is_show_blocked",
                            },
                            "ExpressionAttributeValues": {
                                ":new_value": is_blocked,
                            },
                        },
                    },
                    {
                        "Update": {
                            "Key": {
                                "pk": f"EVENT#{show.event_id}#CITY#{venue.city}",
                                "sk": f"DATE#{show.show_date}#VENUE#{show.venue_id}#SHOW#{show_id}",
                            },
                            "TableName": self.table.name,
                            "UpdateExpression": "SET #is_blocked=:new_value",
                            "ExpressionAttributeNames": {
                                "#is_blocked": "is_show_blocked",
                            },
                            "ExpressionAttributeValues": {
                                ":new_value": is_blocked,
                            },
                        },
                    },
                ]
            )
        except ClientError as e:
            raise
