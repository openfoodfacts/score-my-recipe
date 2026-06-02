from unittest.mock import AsyncMock, Mock, patch

import httpx
from fastapi.testclient import TestClient

from api.api import app

client = TestClient(app)

OFF_RESPONSE = {
    "errors": [],
    "matched_synonyms": {"Italie": "Italie"},
    "status": "success",
    "suggestions": ["Italie"],
    "warnings": [],
}


def test_autocomplete_origins_returns_filtered_response():
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = OFF_RESPONSE

    mock_async_client = AsyncMock()
    mock_async_client.__aenter__.return_value = mock_async_client
    mock_async_client.get.return_value = mock_response

    with patch("api.api.httpx.AsyncClient", return_value=mock_async_client):
        response = client.get("/v1/autocomplete/origins", params={"term": "ital", "lc": "fr"})

    assert response.status_code == 200
    assert response.json() == {
        "matched_synonyms": {"Italie": "Italie"},
        "status": "success",
        "suggestions": ["Italie"],
    }
    mock_async_client.get.assert_awaited_once_with(
        "https://world.openfoodfacts.org/api/v3/taxonomy_suggestions",
        params={
            "tagtype": "origins",
            "term": "ital",
            "lc": "fr",
            "limit": 300,
            "get_synonyms": 1,
        },
    )


def test_autocomplete_origins_errors_and_warnings_not_exposed():
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = OFF_RESPONSE

    mock_async_client = AsyncMock()
    mock_async_client.__aenter__.return_value = mock_async_client
    mock_async_client.get.return_value = mock_response

    with patch("api.api.httpx.AsyncClient", return_value=mock_async_client):
        response = client.get("/v1/autocomplete/origins", params={"term": "ital", "lc": "fr"})

    body = response.json()
    assert "errors" not in body
    assert "warnings" not in body


def test_autocomplete_origins_get_synonyms_not_exposed_in_api():
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = OFF_RESPONSE

    mock_async_client = AsyncMock()
    mock_async_client.__aenter__.return_value = mock_async_client
    mock_async_client.get.return_value = mock_response

    # get_synonyms should be ignored if accidentally passed as a query parameter
    with patch("api.api.httpx.AsyncClient", return_value=mock_async_client):
        response = client.get(
            "/v1/autocomplete/origins",
            params={"term": "ital", "lc": "fr", "get_synonyms": "false"},
        )

    assert response.status_code == 200
    # The upstream call must always use get_synonyms=1 regardless
    _, kwargs = mock_async_client.get.call_args
    assert kwargs["params"]["get_synonyms"] == 1


def test_autocomplete_origins_returns_502_when_off_fails():
    request = httpx.Request("GET", "https://world.openfoodfacts.org/api/v3/taxonomy_suggestions")
    mock_async_client = AsyncMock()
    mock_async_client.__aenter__.return_value = mock_async_client
    mock_async_client.get.side_effect = httpx.RequestError("failure", request=request)

    with patch("api.api.httpx.AsyncClient", return_value=mock_async_client):
        response = client.get("/v1/autocomplete/origins", params={"term": "ital", "lc": "fr"})

    assert response.status_code == 502
    assert response.json() == {"detail": "Open Food Facts API unavailable"}
