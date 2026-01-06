from types_boto3_dynamodb.service_resource import Table
from types_boto3_dynamodb import DynamoDBClient
from botocore.exceptions import ClientError    
from models.shows import Show
from models.venue import Venue


#create
#get show by id
# list by event
# update
#update show booking
class ShowRepository:
    def __init__(self, table:Table,client:DynamoDBClient=None):
        self.table=table
        self.client = client if client else table.meta.client
    def create_show(self,show:Show,venue:Venue):
        #4 insertions
        booked_seats=[]
        show_item={
            "pk":f"SHOW#{show.id}",
            "sk":f"DETAILS",
            "venue_city":venue.city,
            "venue_id":venue.id,
            "event_id":show.event_id,
            "price": show.price,
            "show_date_time":"tba",
            "booked_seats"="empty list"
            
        }