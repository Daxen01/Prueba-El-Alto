from enum import StrEnum
from typing import Annotated

from fastapi import Query
from pydantic import BaseModel


class ProductEnum(StrEnum):
    gasolina_93 = "93"
    gasolina_95 = "95"
    gasolina_97 = "97"
    diesel = "diesel"
    kerosene = "kerosene"


class SearchQuery(BaseModel):
    lat: Annotated[
        float,
        Query(
            description="Latitud del punto de referencia (WGS-84)",
            ge=-90.0,
            le=90.0,
            examples=[-23.65],
        ),
    ]
    lng: Annotated[
        float,
        Query(
            description="Longitud del punto de referencia (WGS-84)",
            ge=-180.0,
            le=180.0,
            examples=[-70.40],
        ),
    ]
    product: Annotated[
        ProductEnum,
        Query(
            description="Tipo de combustible a buscar",
            examples=["93"],
        ),
    ]
    nearest: Annotated[
        bool,
        Query(description="Ordenar resultados por cercanía al punto de referencia"),
    ] = True
    store: Annotated[
        bool,
        Query(description="Filtrar solo estaciones con tienda de conveniencia"),
    ] = False
    cheapest: Annotated[
        bool,
        Query(description="Filtrar solo las estaciones con el menor precio disponible"),
    ] = False
