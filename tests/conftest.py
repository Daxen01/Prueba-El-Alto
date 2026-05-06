"""Fixtures y datos mock compartidos para los tests."""

from unittest.mock import AsyncMock

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.clients.bencina import bencina_client
from app.main import app

# datos mock con la misma estructura que devuelve la API real

MOCK_STATIONS = [
    {
        "id": 100,
        "marca": 5,
        "direccion": " Av. Principal 123",
        "latitud": "-23,650",
        "longitud": "-70,400",
        "region": "Antofagasta",
        "comuna": "Antofagasta",
        "combustibles": [
            {
                "id": 1,
                "nombre_corto": "93",
                "nombre_largo": "Gasolina 93",
                "precio": "1500.000",
                "tipo_atencion": 1,
                "suministra": 1,
            }
        ],
        "servicios": [],
        "atenciones": [],
    },
    {
        "id": 200,
        "marca": 5,
        "direccion": "Calle Secundaria 456",
        "latitud": "-23,700",
        "longitud": "-70,450",
        "region": "Antofagasta",
        "comuna": "Antofagasta",
        "combustibles": [
            {
                "id": 1,
                "nombre_corto": "93",
                "nombre_largo": "Gasolina 93",
                "precio": "1400.000",
                "tipo_atencion": 1,
                "suministra": 1,
            }
        ],
        "servicios": [{"id": 4, "nombre": "Tienda de conveniencia", "estacion_id": 200}],
        "atenciones": [],
    },
]

MOCK_MARCAS = [{"id": 5, "nombre": "COPEC", "activo": 1}]

MOCK_COMBUSTIBLES = [
    {"id": 1, "nombre_corto": "93", "nombre_largo": "Gasolina 93"},
    {"id": 3, "nombre_corto": "DI", "nombre_largo": "Petroleo Diesel"},
]

MOCK_SERVICIOS = [
    {"id": 4, "nombre": "Tienda de conveniencia", "activo": 1},
]


# fixtures para tests de servicio (mockea los métodos del cliente)

@pytest.fixture
def mock_client_methods(monkeypatch):
    """Reemplaza los métodos async de bencina_client con AsyncMock."""
    monkeypatch.setattr(bencina_client, "get_stations", AsyncMock(return_value=MOCK_STATIONS))
    monkeypatch.setattr(bencina_client, "get_marcas", AsyncMock(return_value=MOCK_MARCAS))
    monkeypatch.setattr(bencina_client, "get_servicios", AsyncMock(return_value=MOCK_SERVICIOS))
    monkeypatch.setattr(
        bencina_client, "get_combustibles", AsyncMock(return_value=MOCK_COMBUSTIBLES)
    )


# fixtures para tests de ruta (TestClient + respx)

@pytest.fixture
def mock_http():
    """Intercepta todas las llamadas HTTP al upstream con respx."""
    with respx.mock(base_url="https://api.bencinaenlinea.cl/api", assert_all_called=False) as m:
        m.get("/busqueda_estacion_filtro").mock(
            return_value=httpx.Response(200, json={"data": MOCK_STATIONS})
        )
        m.get("/marca_ciudadano").mock(
            return_value=httpx.Response(200, json={"data": MOCK_MARCAS})
        )
        m.get("/combustible_ciudadano").mock(
            return_value=httpx.Response(200, json={"data": MOCK_COMBUSTIBLES})
        )
        m.get("/servicio_ciudadano").mock(
            return_value=httpx.Response(200, json={"data": MOCK_SERVICIOS})
        )
        yield m


@pytest.fixture
def client(mock_http):
    """TestClient con HTTP mockeado y caché limpio."""
    bencina_client.clear_cache()
    with TestClient(app) as c:
        yield c
