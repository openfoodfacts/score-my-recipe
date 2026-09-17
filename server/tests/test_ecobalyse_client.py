"""Tests for EcobalyseClient."""

from unittest.mock import AsyncMock, patch
import httpx
import pytest

from api.ecobalyse_client import EcobalyseAPIError, EcobalyseClient


def test_ecobalyse_client_headers():
    client_no_token = EcobalyseClient(base_url="https://example.com/api", api_token=None)
    headers = client_no_token._headers()
    assert "Authorization" not in headers
    assert headers["Content-Type"] == "application/json"

    client_with_token = EcobalyseClient(base_url="https://example.com/api", api_token="secret-123")
    headers_with_token = client_with_token._headers()
    assert headers_with_token["Authorization"] == "Bearer secret-123"
    assert headers_with_token["token"] == "secret-123"


@pytest.mark.asyncio
async def test_simulate_food_success():
    client = EcobalyseClient(base_url="https://example.com/api")
    mock_response = httpx.Response(
        status_code=200,
        json={
            "results": {
                "impacts": {
                    "ecs": 0.42,
                    "cch": 0.65,
                }
            }
        },
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        result = await client.simulate_food({"ingredients": [{"id": "uuid-1", "mass": 100}]})

    assert result["results"]["impacts"]["ecs"] == 0.42


@pytest.mark.asyncio
async def test_simulate_food_401_raises_error():
    client = EcobalyseClient(base_url="https://example.com/api")
    mock_response = httpx.Response(
        status_code=401,
        text="Unauthorized",
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        with pytest.raises(EcobalyseAPIError) as exc_info:
            await client.simulate_food({"ingredients": []})

    assert exc_info.value.status_code == 401
    assert "authentication failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_simulate_food_mock_fallback_on_network_error():
    client = EcobalyseClient(base_url="https://example.com/api")
    client.mock_fallback = True

    with patch("httpx.AsyncClient.post", side_effect=httpx.ConnectError("Connection refused")):
        result = await client.simulate_food({"ingredients": [{"id": "uuid-1", "mass": 200}]})

    assert "results" in result
    assert result["results"]["impacts"]["ecs"] > 0
