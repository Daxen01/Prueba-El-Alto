"""Tests unitarios del servicio station_search (los 4 casos + errores)."""

from unittest.mock import AsyncMock

import pytest

from app.clients.bencina import bencina_client
from app.core.exceptions import NoStationsFoundError, ProductNotFoundError
from app.schemas.query import ProductEnum
from app.services.station_search import search_station

# coordenadas iguales a la estación 100, así siempre queda como la más cercana
LAT = -23.650
LNG = -70.400


# casos felices — los 4 escenarios requeridos


@pytest.mark.asyncio
async def test_case1_nearest(mock_client_methods):
    """Case 1: estación más cercana por producto."""
    result = await search_station(lat=LAT, lng=LNG, product=ProductEnum.gasolina_93)

    assert result["success"] is True
    data = result["data"]
    assert data["id"] == "100"
    assert data["compania"] == "COPEC"
    assert data["precios93"] == 1500
    assert data["tiene_tienda"] is False
    assert data["distancia(lineal)"] < 1.0


@pytest.mark.asyncio
async def test_case2_cheapest(mock_client_methods):
    """Case 2: estación más cercana con menor precio por producto."""
    result = await search_station(
        lat=LAT, lng=LNG, product=ProductEnum.gasolina_93, cheapest=True
    )

    data = result["data"]
    # estación 200 tiene precio 1400, queda sola tras el filtro
    assert data["id"] == "200"
    assert data["precios93"] == 1400


@pytest.mark.asyncio
async def test_case3_store(mock_client_methods):
    """Case 3: estación más cercana con tienda por producto."""
    result = await search_station(
        lat=LAT, lng=LNG, product=ProductEnum.gasolina_93, store=True
    )

    data = result["data"]
    # solo la estación 200 tiene tienda
    assert data["id"] == "200"
    assert data["tiene_tienda"] is True
    assert data["tienda"] == {"presente": True}


@pytest.mark.asyncio
async def test_case4_store_and_cheapest(mock_client_methods):
    """Case 4: estación más cercana con tienda y menor precio por producto."""
    result = await search_station(
        lat=LAT, lng=LNG, product=ProductEnum.gasolina_93, store=True, cheapest=True
    )

    data = result["data"]
    assert data["id"] == "200"
    assert data["tiene_tienda"] is True
    assert data["precios93"] == 1400


# estructura de la respuesta


@pytest.mark.asyncio
async def test_response_contains_required_fields(mock_client_methods):
    result = await search_station(lat=LAT, lng=LNG, product=ProductEnum.gasolina_93)
    data = result["data"]

    required = {
        "id", "compania", "direccion", "comuna", "region",
        "latitud", "longitud", "distancia(lineal)", "precios93",
        "tiene_tienda", "tienda",
    }
    assert required.issubset(data.keys())


@pytest.mark.asyncio
async def test_direccion_is_stripped(mock_client_methods):
    result = await search_station(lat=LAT, lng=LNG, product=ProductEnum.gasolina_93)
    # el mock tiene un espacio al inicio en direccion
    assert not result["data"]["direccion"].startswith(" ")


# errores esperados


@pytest.mark.asyncio
async def test_product_not_found_raises(mock_client_methods):
    """No station sells diesel in the mock data → ProductNotFoundError."""
    with pytest.raises(ProductNotFoundError):
        await search_station(lat=LAT, lng=LNG, product=ProductEnum.diesel)


@pytest.mark.asyncio
async def test_store_no_results_raises(mock_client_methods):
    """Station with 95 exists but has no tienda → NoStationsFoundError."""
    station_no_tienda = {
        "id": 300,
        "marca": 5,
        "direccion": "Test St",
        "latitud": "-23.65",
        "longitud": "-70.40",
        "region": "Test",
        "comuna": "Test",
        "combustibles": [
            {
                "id": 7, "nombre_corto": "95", "nombre_largo": "Gasolina 95",
                "precio": "1600.000", "tipo_atencion": 1, "suministra": 1,
            }
        ],
        "servicios": [],
        "atenciones": [],
    }
    bencina_client.get_stations = AsyncMock(return_value=[station_no_tienda])

    with pytest.raises(NoStationsFoundError):
        await search_station(lat=LAT, lng=LNG, product=ProductEnum.gasolina_95, store=True)
