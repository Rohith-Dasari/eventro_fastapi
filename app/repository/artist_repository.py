from typing import Optional
from app.models.artists import Artist
from typing import Dict, List, Optional
import time
from types_boto3_dynamodb.service_resource import Table
from botocore.exceptions import ClientError


class ArtistRepository:
    def __init__(self, table: Table, client=None):
        self.table = table
        self.client = client or table.meta.client

    def get_by_id(self, artist_id: str) -> Optional[Artist]:
        resp = self.table.get_item(Key={"pk": f"ARTIST#{artist_id}", "sk": "DETAILS"})

        item = resp.get("Item")
        if not item:
            return None

        return Artist(
            id=artist_id,
            name=item["name"],
            bio=item.get("bio"),
        )

    def batch_get_by_ids(self, artist_ids: List[str]) -> Dict[str, Artist]:
        keys = [
                    {
                        "pk": f"ARTIST#{aid}",
                        "sk": "DETAILS",
                    }
                    for aid in artist_ids
                ]
        request_items = {
            self.table.name: {
                "Keys": keys
            }
        }
        artists: Dict[str, Artist] = {}
        resp = self.client.batch_get_item(RequestItems=request_items)
        items = resp["Responses"].get(self.table.name, [])
        for item in items:
            artist_id = item["pk"].replace("ARTIST#", "")
            artists[artist_id] = Artist(
                id=artist_id,
                name=item["name"],
                bio=item.get("bio", {}),
            )
        return artists

    def add_artist(self, artist: Artist) -> Artist:
        try:
            self.table.put_item(
                Item={
                    "pk": f"ARTIST#{artist.id}",
                    "sk": "DETAILS",
                    "name": artist.name,
                    "bio": artist.bio,
                },
            )
        except ClientError as e:
            raise
        return artist
