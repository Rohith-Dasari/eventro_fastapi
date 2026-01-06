from models.venue import Venue
from botocore.exceptions import ClientError
import logging
from types_boto3_dynamodb.service_resource import Table
from types_boto3_dynamodb import DynamoDBClient
from typing import Optional, List
from boto3.dynamodb.conditions import Key


class VenueRepository:
    def __init__(self, table: Table, client: DynamoDBClient = None):
        self.table = table
        self.client = client if client else table.meta.client

    def add_venue(self, venue: Venue):
        user_item = {
            "pk": f"USER#{venue.host_id}",
            "sk": f"VENUE#{venue.id}",
            "venue_name": venue.name,
            "is_blocked": venue.is_blocked,
            "venue_city": venue.city,
            "venue_state": venue.state,
            "is_seat_layout_required": venue.is_seat_layout_required,
        }
        venue_item = {
            "pk": f"VENUE#{venue.id}",
            "sk": "DETAILS",
            "host_id": venue.host_id,
            "venue_name": venue.name,
            "is_blocked": venue.is_blocked,
            "venue_city": venue.city,
            "venue_state": venue.state,
            "is_seat_layout_required": venue.is_seat_layout_required,
        }
        try:
            self.client.transact_write_items(
                TransactItems=[
                    {
                        "Put": {
                            "TableName": self.table.name,
                            "Item": user_item,
                        },
                    },
                    {
                        "Put": {
                            "TableName": self.table.name,
                            "Item": venue_item,
                        },
                    },
                ]
            )
        except ClientError as e:
            pass

    def get_venue_by_id(self, venue_id: str):
        try:
            response = self.table.get_item(
                Key={"pk": f"VENUE#{venue_id}", "sk": f"DETAILS"}
            )
        except ClientError as err:
            raise
        item = response.get("Item")
        if not item:
            return None
        return Venue(
            id=item["pk"].split("#", 1)[1],
            name=item["venue_name"],
            host_id=item["host_id"],
            city=item["venue_city"],
            state=item["venue_state"],
            is_blocked=item["is_blocked"],
            is_seat_layout_required=item["is_seat_layout_required"],
        )

    def get_host_venues(self, host_id: str) -> List[Venue]:
        try:
            response = self.table.query(
                KeyConditionExpression=(
                    Key("pk").eq(f"USER#{host_id}") & Key("sk").begins_with("VENUE#")
                )
            )
        except ClientError as e:
            raise
        items = response.get("Items", [])
        if not items:
            return None
        venues = []
        for item in items:
            venue = Venue(
                id=item["sk"].split("#", 1)[1],
                host_id=item["pk"].split("#", 1)[1],
                name=item["venue_name"],
                city=item["venue_city"],
                state=item["venue_state"],
                is_blocked=item["is_blocked"],
                is_seat_layout_required=item["is_seat_layout_required"],
            )
            venues.append(venue)
        return venue

    def update_venue(self, venue_id: str, host_id: str, is_blocked: bool):
        try:
            self.client.transact_write_items(
                TransactItems=[
                    {
                        "Update": {
                            "TableName": self.table.name,
                            "Key": {"pk": f"VENUE#{venue_id}", "sk": "DETAILS"},
                            "UpdateExpression": "SET #is_blocked=:new_value",
                            "ExpressionAttributeNames": {
                                "#is_blocked": "is_blocked",
                                "#host_id": "host_id",
                            },
                            "ExpressionAttributeValues": {
                                ":new_value": is_blocked,
                                ":host_id": host_id,
                            },
                            "ConditionExpression": "attribute_exists(pk) AND #host_id = :host_id",
                        }
                    },
                    {
                        "Update": {
                            "TableName": self.table.name,
                            "Key": {"pk": f"USER#{host_id}", "sk": f"VENUE#{venue_id}"},
                            "UpdateExpression": "SET #is_blocked=:new_value",
                            "ExpressionAttributeNames": {"#is_blocked": "is_blocked"},
                            "ExpressionAttributeValues": {":new_value": is_blocked},
                            "ConditionExpression": "attribute_exists(pk)",
                        }
                    },
                ]
            )

        except ClientError as e:
            raise

    def delete_venue(self, venue_id: str, host_id: str):
        try:
            self.client.transact_write_items(
                TransactItems=[
                    {
                        "Delete": {
                            "Key": {
                                "pk": f"VENUE#{venue_id}",
                                "sk": f"DETAILS",
                            }
                        },
                    },
                    {
                        "Delete": {
                            "Key": {
                                "pk": f"USER#{host_id}",
                                "sk": f"VENUE#{venue_id}",
                            }
                        },
                    },
                ]
            )
        except ClientError as e:
            raise
