from typing import Optional
from models import Artist
from typing import Dict,List,Optional
import time

class ArtistRepository:
    def __init__(self, table, client=None):
        self.table = table
        self.client = client or table.meta.client

    def get_by_id(self, artist_id: str) -> Optional[Artist]:
        resp = self.client.get_item(
            TableName=self.table.name,
            Key={
                "pk": {"S": f"ARTIST#{artist_id}"},
                "sk": {"S": "DETAILS"},
            },
        )

        item = resp.get("Item")
        if not item:
            return None

        return Artist(
            id=artist_id,
            name=item["name"]["S"],
            bio=item.get("bio", {}).get("S"),
        )
        
    def batch_get_by_ids(self, artist_ids: List[str]) -> Dict[str, Artist]:
        keys = [
            {
                "pk": {"S": f"ARTIST#{aid}"},
                "sk": {"S": "DETAILS"},
            }
            for aid in artist_ids
        ]

        request = {
            self.table.name: {
                "Keys": keys
            }
        }

        artists: Dict[str, Artist] = {}
        unprocessed = request

        while unprocessed:
            resp = self.client.batch_get_item(
                RequestItems=unprocessed
            )

            items = resp["Responses"].get(self.table.name, [])
            for item in items:
                artist_id = item["pk"]["S"].replace("ARTIST#", "")
                artists[artist_id] = Artist(
                    id=artist_id,
                    name=item["name"]["S"],
                    bio=item.get("bio", {}).get("S"),
                )

            unprocessed = resp.get("UnprocessedKeys")
            if unprocessed:
                time.sleep(0.05) 

        return artists

