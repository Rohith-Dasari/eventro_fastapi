from models.events import Event
from botocore.exceptions import ClientError
import logging
from types_boto3_dynamodb.service_resource import Table
from types_boto3_dynamodb import DynamoDBClient
from typing import Optional, List
from boto3.dynamodb.conditions import Key


logger = logging.getLogger(__name__)


class EventRepository:
    def __init__(self, table: Table, client: DynamoDBClient = None):
        self.table = table
        self.client = client if client else table.meta.client

    def add_event(self, event: Event):
        event_item = {
            "pk": f"EVENT#{event.id}",
            "sk": "DETAILS",
            "event_name": event.name,
            "description": event.description,
            "duration": event.duration,
            "category": event.category,
            "is_event_blocked": event.is_blocked,
            "artist_ids": event.artist_ids,
            "artist_names": event.artist_names,
        }
        name_index_item = {
            "pk": "EVENTS",
            "sk": f"EVENT_NAME#{event.name}#EVENT_ID#{event.id}",
            "description": event.description,
            "duration": event.duration,
            "category": event.category,
            "is_event_blocked": event.is_blocked,
            "artist_ids": event.artist_ids,
            "artist_names": event.artist_names,
        }
        transact_items = [
            {
                "Put": {
                    "TableName": self.table.name,
                    "Item": event_item,
                    "ConditionExpression": "attribute_not_exists(pk)",
                }
            },
            {
                "Put": {
                    "TableName": self.table.name,
                    "Item": name_index_item,
                }
            },
        ]
        try:
            self.client.transact_write_items(TransactItems=transact_items)
        except ClientError as e:
            raise

    def get_by_id(self, event_id: str) -> Optional[Event]:
        try:
            resp = self.table.get_item(Key={"pk": f"EVENT#{event_id}", "sk": "DETAILS"})
        except ClientError as e:
            raise

        item = resp.get("Item")
        if not item:
            return None

        return Event(
            id=event_id,
            name=item["event_name"],
            description=item.get("description", ""),
            duration=item.get("duration", 0),
            category=item.get("category", ""),
            is_blocked=item.get("is_event_blocked", False),
            artist_ids=item.get("artist_ids", []),
            artist_names=item.get("artist_names", []),
        )

    def get_events_by_name(self, name: str) -> List[Event]:
        prefix = f"EVENT_NAME#{name}"
        try:
            resp = self.table.query(
                KeyConditionExpression=Key("pk").eq("EVENTS")
                & Key("sk").begins_with(prefix),
            )
        except ClientError as e:
            raise

        items = resp.get("Items", [])

        events = []
        event_ids=[]
        for item in items:
            event_id = item["sk"].split("#EVENT_ID#")[-1]
            event_ids.append(event_id)
        events = self._batch_get_events(event_ids=event_ids)
        return events

    def get_events_of_host(self, host_id: str) -> List[Event]:
        prefix = f"EVENT#"
        try:
            resp = self.table.query(
                KeyConditionExpression=Key("pk").eq(f"HOST#{host_id}")
                & Key("sk").begins_with(prefix)
            )
        except ClientError as e:
            raise
        event_ids = []
        items = resp.get("Items", [])
        if not items:
            return []
        for item in items:
            event_id = item["sk"].split("#")[-1]
            event_ids.append(event_id)
        events = self._batch_get_events(event_ids=event_ids)
        return events

    def _batch_get_events(self, event_ids: List[str]) -> List[Event]:
        if not event_ids:
            return []
        keys = []
        for event_id in event_ids:
            keys.append({"pk": f"EVENT#{event_id}", "sk": "DETAILS"})

        request_items = {
            self.table.name: {
                "Keys": keys,
            }
        }
        resp = self.client.batch_get_item(RequestItems=request_items)
        items = resp.get("Responses", {}).get(self.table.name, [])
        while resp.get("UnprocessedKeys"):
            resp = self.client.batch_get_item(RequestItems=resp["UnprocessedKeys"])
            items.extend(resp.get("Responses", {}).get(self.table.name, []))
        events: Event = []
        for item in items:
            events.append(
                Event(
                    id=item["pk"].split("#")[1],
                    name=item.get("event_name", ""),
                    description=item.get("description", ""),
                    duration=item.get("duration", 0),
                    category=item.get("category", ""),
                    is_blocked=item.get("is_event_blocked", False),
                    artist_ids=item.get("artist_ids", []),
                    artist_names=item.get("artist_names", []),
                )
            )
        return events

    def get_events_by_city_and_name(self, city: str,name: str="") -> Event:
        prefix = f"NAME#{name}"
        try:
            resp = self.table.query(
                KeyConditionExpression=Key("pk").eq(f"CITY#{city}")
                & Key("sk").begins_with(prefix)
            )
        except ClientError as e:
            raise
        items = resp.get("Items", [])
        if not items:
            return [] 
        
        event_ids=[]
        for item in items:
            id=item["sk"].split("ID#")[-1]
            event_ids.append(id)
        events = self._batch_get_events(event_ids=event_ids)
        return events

    def update_event(self, event_id: str, is_blocked: bool) -> Event:
        try:
            self.client.transact_write_items(
                TransactItems=[
                    {
                        "Update": {
                            "Key": {"pk": f"EVENT#{event_id}", "sk": "DETAILS"},
                            "TableName": self.table.name,
                            "UpdateExpression": "SET #is_blocked=:new_value",
                            "ExpressionAttributeNames": {
                                "#is_blocked": "is_event_blocked",
                            },
                            "ExpressionAttributeValues": {
                                ":new_value": is_blocked,
                            },
                            "ConditionExpression": "attribute_exists(pk)",
                        }
                    },
                ]
            )
        except ClientError as e:
            raise
