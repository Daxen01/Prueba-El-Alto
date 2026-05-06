"""Tests de integración para /api/stations/search."""

import httpx
from fastapi.testclient import TestClient

from app.clients.bencina import bencina_client
from app.main import app

BASE_URL = "/api/stations/search"
LAT = -23.650
LNG = -70.400


# casos felices


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_case1_nearest(client):
    """Case 1: nearest station with product 93."""
    resp = client.get(BASE_URL, params={"lat": LAT, "lng": LNG, "product": "93"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["id"] == "100"
    assert body["data"]["precios93"] == 1500


def test_case2_cheapest(client):
    """Case 2: nearest among cheapest for product 93."""
    resp = client.get(
        BASE_URL, params={"lat": LAT, "lng": LNG, "product": "93", "cheapest": "true"}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == "200"
    assert resp.json()["data"]["precios93"] == 1400


def test_case3_store(client):
    """Case 3: nearest station with tienda for product 93."""
    resp = client.get(
        BASE_URL, params={"lat": LAT, "lng": LNG, "product": "93", "store": "true"}
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["id"] == "200"
    assert data["tiene_tienda"] is True


def test_case4_store_and_cheapest(client):
    """Case 4: nearest cheapest station with tienda for product 93."""
    resp = client.get(
        BASE_URL,
        params={"lat": LAT, "lng": LNG, "product": "93", "store": "true", "cheapest": "true"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["id"] == "200"
    assert data["tiene_tienda"] is True
    assert data["precios93"] == 1400


# errores de validación (422)


def test_invalid_product_returns_422(client):
    resp = client.get(BASE_URL, params={"lat": LAT, "lng": LNG, "product": "hidrogeno"})
    assert resp.status_code == 422


def test_lat_out_of_range_returns_422(client):
    resp = client.get(BASE_URL, params={"lat": 999, "lng": LNG, "product": "93"})
    assert resp.status_code == 422


def test_missing_required_params_returns_422(client):
    resp = client.get(BASE_URL)
    assert resp.status_code == 422


# no encontrado (404)


def test_product_not_available_returns_404(client):
    """diesel is not in mock data → 404 with error body."""
    resp = client.get(BASE_URL, params={"lat": LAT, "lng": LNG, "product": "diesel"})
    assert resp.status_code == 404
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "PRODUCT_NOT_FOUND"


# error del upstream (502)


def test_upstream_error_returns_502(mock_http):
    """When the upstream returns 503, we propagate as 502."""
    mock_http.get("/busqueda_estacion_filtro").mock(
        return_value=httpx.Response(503, text="Service Unavailable")
    )
    bencina_client.clear_cache()

    with TestClient(app) as c:
        resp = c.get(BASE_URL, params={"lat": LAT, "lng": LNG, "product": "93"})

    assert resp.status_code == 502
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "UPSTREAM_ERROR"
