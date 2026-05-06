from typing import Any

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail


class SearchResponse(BaseModel):
    success: bool = True
    data: dict[str, Any]

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "data": {
                    "id": "100",
                    "compania": "COPEC",
                    "direccion": "San Martin Esq. Uribe",
                    "comuna": "Antofagasta",
                    "region": "Antofagasta",
                    "latitud": -23.6491868026,
                    "longitud": -70.4011811037,
                    "distancia(lineal)": 0.523,
                    "precios93": 1657,
                    "tiene_tienda": False,
                    "tienda": None,
                },
            }
        }
    }
