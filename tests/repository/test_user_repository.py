from unittest.mock import MagicMock
import pytest
from botocore.exceptions import ClientError

from app.repository.user_repository import UserRepository
from models.users import User, Role


def make_table_mock():
    table = MagicMock()
    table.name = "users"
    table.meta.client = MagicMock()
    return table


def sample_user():
    return User(
        user_id="u1",
        username="alice",
        email="alice@example.com",
        phone_number="1234567890",
        password="hashed",
        role=Role.CUSTOMER,
        is_blocked=False,
    )


def test_add_user_calls_transact_write_items():
    table = make_table_mock()
    repo = UserRepository(table=table)
    user = sample_user()

    repo.add_user(user)

    table.meta.client.transact_write_items.assert_called_once()
    args, kwargs = table.meta.client.transact_write_items.call_args
    transact = kwargs["TransactItems"]
    assert len(transact) == 2
    assert transact[0]["Put"]["Item"]["pk"] == f"EMAIL#{user.email}"
    assert transact[1]["Put"]["Item"]["pk"] == f"USER#{user.user_id}"


def test_add_user_raises_on_client_error():
    table = make_table_mock()
    error = ClientError({"Error": {"Code": "Boom", "Message": "fail"}}, "TransactWriteItems")
    table.meta.client.transact_write_items.side_effect = error
    repo = UserRepository(table=table)

    with pytest.raises(ClientError):
        repo.add_user(sample_user())


def test_get_by_id_returns_user():
    table = make_table_mock()
    table.get_item.return_value = {
        "Item": {
            "pk": "USER#u1",
            "sk": "DETAILS",
            "username": "alice",
            "email": "alice@example.com",
            "phone_number": "1234567890",
            "password": "hashed",
            "role": "customer",
            "is_blocked": False,
        }
    }
    repo = UserRepository(table=table)

    user = repo.get_by_id("u1")

    assert isinstance(user, User)
    assert user.user_id == "u1"
    assert user.username == "alice"
    assert user.role == Role.CUSTOMER
    table.get_item.assert_called_once_with(Key={"pk": "USER#u1", "sk": "DETAILS"})


def test_get_by_id_missing_returns_none():
    table = make_table_mock()
    table.get_item.return_value = {}
    repo = UserRepository(table=table)

    assert repo.get_by_id("missing") is None


def test_get_by_mail_queries_and_returns_user():
    table = make_table_mock()
    table.query.return_value = {
        "Items": [{"pk": "EMAIL#alice@example.com", "sk": "USER#u1"}]
    }
    table.get_item.return_value = {
        "Item": {
            "pk": "USER#u1",
            "sk": "DETAILS",
            "username": "alice",
            "email": "alice@example.com",
            "phone_number": "1234567890",
            "password": "hashed",
            "role": "customer",
            "is_blocked": False,
        }
    }
    repo = UserRepository(table=table)

    user = repo.get_by_mail("alice@example.com")

    assert isinstance(user, User)
    assert user.user_id == "u1"
    table.query.assert_called_once()
    table.get_item.assert_called_once_with(Key={"pk": "USER#u1", "sk": "DETAILS"})


def test_get_by_mail_missing_returns_none():
    table = make_table_mock()
    table.query.return_value = {"Items": []}
    repo = UserRepository(table=table)

    user = repo.get_by_mail("missing@example.com")

    assert user is None
    table.query.assert_called_once()


def test_get_by_mail_item_present_but_details_missing_returns_none():
    table = make_table_mock()
    table.query.return_value = {"Items": [{"pk": "EMAIL#a@b.com", "sk": "USER#u1"}]}
    table.get_item.return_value = {}
    repo = UserRepository(table=table)

    user = repo.get_by_mail("a@b.com")

    assert user is None
    table.query.assert_called_once()
    table.get_item.assert_called_once_with(Key={"pk": "USER#u1", "sk": "DETAILS"})


def test_get_by_id_raises_client_error_when_table_fails():
    table = make_table_mock()
    error = ClientError({"Error": {"Code": "Boom", "Message": "fail"}}, "GetItem")
    table.get_item.side_effect = error
    repo = UserRepository(table=table)

    with pytest.raises(ClientError):
        repo.get_by_id("u1")
