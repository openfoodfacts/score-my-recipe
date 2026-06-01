from unittest.mock import AsyncMock, Mock, patch

import httpx
from fastapi.testclient import TestClient

from api.api import app

client = TestClient(app)


def test_autocomplete_origins_returns_openfoodfacts_response():
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"tags": [{"id": "en:italy", "name": "Italie"}]}

    mock_async_client = AsyncMock()
    mock_async_client.__aenter__.return_value = mock_async_client
    mock_async_client.get.return_value = mock_response

    with patch("api.api.httpx.AsyncClient", return_value=mock_async_client):
        response = client.get("/v1/autocomplete/origins", params={"term": "ital", "lc": "fr"})

    assert response.status_code == 200
    assert response.json() == {"tags": [{"id": "en:italy", "name": "Italie"}]}
    mock_async_client.get.assert_awaited_once_with(
        "https://world.openfoodfacts.org/cgi/suggest.pl",
        params={"tagtype": "origins", "term": "ital", "lc": "fr", "limit": 300},
    )


def test_autocomplete_origins_returns_502_when_off_fails():
    request = httpx.Request("GET", "https://world.openfoodfacts.org/cgi/suggest.pl")
    mock_async_client = AsyncMock()
    mock_async_client.__aenter__.return_value = mock_async_client
    mock_async_client.get.side_effect = httpx.RequestError("failure", request=request)

    with patch("api.api.httpx.AsyncClient", return_value=mock_async_client):
        response = client.get("/v1/autocomplete/origins", params={"term": "ital", "lc": "fr"})

    assert response.status_code == 502
    assert response.json() == {"detail": "Open Food Facts API unavailable"}
