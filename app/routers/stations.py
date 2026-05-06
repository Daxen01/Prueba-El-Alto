from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.schemas.query import SearchQuery
from app.schemas.response import ErrorResponse, SearchResponse
from app.services.station_search import search_station

router = APIRouter(prefix="/api/stations", tags=["Estaciones"])


@router.get(
    "/search",
    response_model=SearchResponse,
    summary="Buscar estación de combustible",
    description=(
        "Retorna la estación que mejor cumple los criterios dados. "
        "Combina filtros de producto, tienda y precio mínimo con ordenamiento por distancia. "
        "Implementa los 4 casos de búsqueda según los flags `nearest`, `store` y `cheapest`."
    ),
    responses={
        200: {"model": SearchResponse, "description": "Estación encontrada"},
        404: {"model": ErrorResponse, "description": "Sin resultados para los criterios dados"},
        422: {"description": "Parámetros de entrada inválidos"},
        502: {"model": ErrorResponse, "description": "Error al contactar la API upstream"},
    },
)
async def search(query: SearchQuery = Depends()) -> JSONResponse:
    result = await search_station(
        lat=query.lat,
        lng=query.lng,
        product=query.product,
        nearest=query.nearest,
        store=query.store,
        cheapest=query.cheapest,
    )
    return JSONResponse(content=result)
