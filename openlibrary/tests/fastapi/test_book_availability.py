"""Tests for the /availability/v2 FastAPI endpoint (internal API)."""

from unittest.mock import patch

import pytest

from openlibrary.fastapi.internal.api import router  # noqa: F401


@pytest.fixture
def mock_get_availability():
    """Patch the legacy lending function used by both GET and POST handlers."""
    with patch("openlibrary.fastapi.internal.api.lending.get_availability") as mock:
        yield mock


class TestBookAvailabilityEndpoint:
    """Tests for GET and POST /availability/v2."""

    @pytest.mark.parametrize(
        ("id_type", "ids_str", "expected_ids"),
        [
            ("openlibrary_work", "OL1W", ["OL1W"]),
            ("openlibrary_edition", "OL1M,OL2M", ["OL1M", "OL2M"]),
            (
                "identifier",
                "isbn:9780140328721,ocaid:aliceinwonderla00carr",
                ["isbn:9780140328721", "ocaid:aliceinwonderla00carr"],
            ),
        ],
    )
    def test_get_all_valid_id_types(self, fastapi_client, mock_get_availability, id_type, ids_str, expected_ids):
        """All three id_type values are accepted and passed correctly."""
        mock_get_availability.return_value = {"OL1W": {"status": "open", "is_previewable": True}}

        response = fastapi_client.get("/availability/v2", params={"type": id_type, "ids": ids_str})
        response.raise_for_status()

        mock_get_availability.assert_called_once_with(id_type, expected_ids)

    def test_get_availability_comma_separated(self, fastapi_client, mock_get_availability):
        mock_get_availability.return_value = {"id1": {"status": "open"}}
        response = fastapi_client.get("/availability/v2?type=identifier&ids=id1,id2,id3")
        response.raise_for_status()
        mock_get_availability.assert_called_once_with("identifier", ["id1", "id2", "id3"])

    def test_get_availability_empty_ids(self, fastapi_client, mock_get_availability):
        response = fastapi_client.get("/availability/v2?type=identifier&ids=")
        assert response.status_code == 422
        mock_get_availability.assert_not_called()

    def test_post_availability_valid(self, fastapi_client, mock_get_availability):
        mock_get_availability.return_value = {"OL1M": {"status": "borrow_available"}}
        payload = {"ids": ["/books/OL1M", "/books/OL2M"]}

        response = fastapi_client.post("/availability/v2?type=openlibrary_edition", json=payload)
        response.raise_for_status()

        mock_get_availability.assert_called_once_with("openlibrary_edition", payload["ids"])

    def test_post_availability_empty_ids(self, fastapi_client, mock_get_availability):
        response = fastapi_client.post("/availability/v2?type=identifier", json={"ids": []})
        assert response.status_code == 422
        mock_get_availability.assert_not_called()

    def test_invalid_id_type(self, fastapi_client, mock_get_availability):
        """Invalid Literal value for id_type → FastAPI 422 validation error."""
        # Test GET
        response = fastapi_client.get("/availability/v2?type=invalid")
        assert response.status_code == 422

        # Test POST
        response = fastapi_client.post("/availability/v2?type=invalid", json={"ids": ["id1"]})
        assert response.status_code == 422
        mock_get_availability.assert_not_called()

    def test_type_alias_required(self, fastapi_client, mock_get_availability):
        """Query param must be 'type' (not 'id_type') because of Query(alias='type')."""
        response = fastapi_client.get("/availability/v2?id_type=openlibrary_work&ids=id1")
        assert response.status_code == 422
        mock_get_availability.assert_not_called()
