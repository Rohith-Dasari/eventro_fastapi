import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_venue_service
from unittest.mock import MagicMock
from app.models.venue import Venue
from app.dependencies import get_current_user
from app.custom_exceptions.generic import NotFoundException
from botocore.exceptions import ClientError


class TestVenuesRouter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        self.mock_get_venue_service = MagicMock()
        app.dependency_overrides[get_venue_service] = (
            lambda: self.mock_get_venue_service
        )
        self.mock_get_current_user = MagicMock()
        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": "u1",
            "role": "host",
        }

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_add_venue_host_calls_service(self):
        venue = Venue(
            id="1",
            host_id="u1",
            name="n",
            city="c",
            state="s",
            is_blocked=False,
            is_seat_layout_required=True,
        )
        self.mock_get_venue_service.add_venue.return_value = venue

        payload = {
            "name": "n",
            "city": "c",
            "state": "NYs",
            "is_seat_layout_required": True,
        }

        resp = self.client.post("/venues", json=payload)

        assert resp.status_code == 201
        body = resp.json()
        assert body["message"] == "added venue successfully"
        assert body["data"]["name"] == payload["name"]

    def test_get_venue_by_id_calls_service(self):
        venue = Venue(
            id="1",
            host_id="u1",
            name="n",
            city="c",
            state="s",
            is_blocked=False,
            is_seat_layout_required=True,
        )
        self.mock_get_venue_service.get_venue_by_id.return_value = venue

        resp = self.client.get("/venues/v1")

        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["name"] == "n"

    def test_update_venue_calls_service(self):
        self.mock_get_venue_service.get_venue_by_id.return_value = None

        resp = self.client.patch("/venues/v1", json={"is_blocked": True})

        assert resp.status_code == 200
        assert resp.json()["message"] == "successfully updated v1"

    def test_delete_venue_calls_service(self):
        self.mock_get_venue_service.delete.return_value = None

        resp = self.client.delete("/venues/v1")

        assert resp.status_code == 200
        assert resp.json()["message"] == "successfully deleted v1"

    def test_get_venue_not_found_uses_handler(self):
        self.mock_get_venue_service.get_venue_by_id.side_effect = NotFoundException(
            resource=Venue, identifier="missing", status_code=404
        )

        resp = self.client.get("/venues/missing")

        assert resp.status_code == 404

    def test_update_venue_not_found(self):
        self.mock_get_venue_service.update_venue.side_effect = NotFoundException(
            resource=Venue, identifier="missing", status_code=404
        )

        resp = self.client.patch("/venues/missing", json={"is_blocked": True})

        assert resp.status_code == 404

    def test_delete_venue_client_error(self):
        self.mock_get_venue_service.delete_venue.side_effect = ClientError(
            error_response={
                "Error": {
                    "Code": "ConditionalCheckFailedException",
                    "Message": "Condition failed",
                }
            },
            operation_name="DeleteItem",
        )

        resp = self.client.delete("/venues/v1")

        assert resp.status_code == 500
