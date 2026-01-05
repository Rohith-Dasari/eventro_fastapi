from abc import ABC, abstractmethod
from models.events import Event
from botocore.exceptions import ClientError
import logging
from types_boto3_dynamodb.service_resource import Table
from types_boto3_dynamodb import DynamoDBClient
from typing import Optional,List
from boto3.dynamodb.conditions import Key

#update,delete

#get events of host
#get events by city
#add host event
#add city event



logger = logging.getLogger(__name__)
class EventRepository:
    def __init__(self, table: Table, client: DynamoDBClient = None):
        self.table = table
        self.client = client if client else table.meta.client
    
    def add_event(self,event:Event):
        event_item = {
            "pk": f"EVENT#{event.id}",
            "sk": "DETAILS",
            "event_name": event.name,
            "description": event.description,
            "duration": event.duration,
            "category": event.category,
            "is_blocked": event.is_blocked,
            "artist_ids": event.artist_ids,
            "artist_names": event.artist_names,
        }
        name_index_item = {
            "pk": "EVENTS",
            "sk": f"EVENT_NAME#{event.name}#EVENT_ID#{event.id}",
            "description": event.description,
            "duration": event.duration,
            "category": event.category,
            "is_blocked": event.is_blocked,
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
            self.client.transact_write_items(
                TransactItems=transact_items
            )
        except ClientError as e:
            raise
        
    def get_by_id(self, event_id: str) -> Optional[Event]:
        try:
            resp = self.table.get_item(
                Key={
                    "pk": f"EVENT#{event_id}",
                    "sk": "DETAILS"
                }
            )
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
            is_blocked=item.get("is_blocked", False),
            artist_ids=item.get("artist_ids", []),
            artist_names=item.get("artist_names", []),
        )
        
    def get_events_by_name(self, name: str) -> List[Event]:
        prefix = f"EVENT_NAME#{name}"
        try:
            resp = self.table.query(
                KeyConditionExpression=Key("pk").eq("EVENTS") & Key("sk").begins_with(prefix),
            )
        except ClientError as e:
            raise

        items = resp.get("Items", [])

        events = []
        for item in items:
            events.append(Event(
                id=item["sk"].split("#")[-1], 
                name=item.get("event_name", ""),
                description=item.get("description", ""),
                duration=item.get("duration", 0),
                category=item.get("category", ""),
                is_blocked=item.get("is_blocked", False),
                artist_ids=item.get("artist_ids", []),
                artist_names=item.get("artist_names", []),
            ))
        return events
    
        
        