import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.clients.bencina import bencina_client
from app.core.config import settings
from app.core.exceptions import AppError, app_error_handler, generic_error_handler
from app.routers import stations

logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    bencina_client.start()
    yield
    await bencina_client.stop()


app = FastAPI(
    title="API Bencina en Línea",
    description=(
        "Búsqueda de estaciones de combustible por ubicación geográfica. "
        "Datos obtenidos en tiempo real desde **bencinaenlinea.cl**.\n\n"
        "### Casos de búsqueda disponibles\n"
        "| Flags | Descripción |\n"
        "|---|---|\n"
        "| `nearest=true` | Estación más cercana con el producto |\n"
        "| `cheapest=true` | Estación más cercana entre las de menor precio |\n"
        "| `store=true` | Estación más cercana con tienda |\n"
        "| `store=true&cheapest=true` | Estación más cercana con tienda y menor precio |"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, generic_error_handler)

app.include_router(stations.router)


@app.get("/health", tags=["Infraestructura"], summary="Health check")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "bencina-api", "version": "1.0.0"})
