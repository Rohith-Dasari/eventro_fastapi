from abc import ABC, abstractmethod
from models.users import User, Role
from botocore.exceptions import ClientError
import logging
from types_boto3_dynamodb.service_resource import Table
from types_boto3_dynamodb import DynamoDBClient
from typing import Optional

logger = logging.getLogger(__name__)


class UserRepository(ABC):
    @abstractmethod
    def add_user(self, user: User) -> Optional[User]:
        pass

    @abstractmethod
    def get_by_mail(self, mail: str) -> Optional[User]:
        pass

    @abstractmethod
    def get_by_id(self, user_id: str) -> Optional[User]:
        pass


class UserRepositoryDDB(UserRepository):
    def __init__(self, table: Table, client: DynamoDBClient = None):
        self.table = table
        self.client = client if client else table.meta.client

    def add_user(self, user: User):
        try:
            self.client.transact_write_items(
                TransactItems=[
                    {
                        "Put": {
                            "TableName": self.table.name,
                            "Item": {
                                "pk": f"EMAIL#{user.email}",
                                "sk": f"USER#{user.user_id}",
                            },
                            "ConditionExpression": "attribute_not_exists(pk)",
                        }
                    },
                    {
                        "Put": {
                            "TableName": self.table.name,
                            "Item": {
                                "pk": f"USER#{user.user_id}",
                                "sk": "DETAILS",
                                "username": user.username,
                                "email": user.email,
                                "phone_number": user.phone_number,
                                "password": user.password,
                                "role": user.role.value,
                                "is_blocked": user.is_blocked,
                            },
                            "ConditionExpression": "attribute_not_exists(pk)",
                        }
                    },
                ]
            )

        except ClientError as err:
            logger.error(
                "couldn't add user %s. Error: %s",
                user.email,
                err.response["Error"]["Message"],
            )
            raise

    def get_by_mail(self, mail: str) -> Optional[User]:
        try:
            response = self.table.get_item(Key={"pk": f"EMAIL#{mail}", "sk": f"USER#"})

        except ClientError as err:
            logger.error("Error retrieving user by mail %s: %s", mail, err)
            raise

        item = response.get("Item")
        if not item:
            return None
        user_id = item["sk"].split("#", 1)[1]
        return self.get_by_id(user_id=user_id)

    def get_by_id(self, user_id: str) -> Optional[User]:
        try:
            response = self.table.get_item(
                Key={"pk": f"USER#{user_id}", "sk": "DETAILS"}
            )
        except ClientError as err:
            raise
        item = response.get("Item")
        if not item:
            return None

        return self._to_domain(item=item)

    @staticmethod
    def _to_domain(item: dict) -> User:
        return User(
            user_id=item["pk"].split("#", 1)[1],
            username=item["username"],
            email=item["email"],
            phone_number=item.get("phone_number"),
            role=Role(item["role"]),
            is_blocked=item["is_blocked"],
            password=item["password"],
        )
