import logging
from time import monotonic
from typing import Any

import httpx
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.exceptions import UpstreamError

logger = logging.getLogger(__name__)

# errores de red que vale la pena reintentar
_RETRYABLE = (httpx.ConnectError, httpx.TimeoutException, httpx.RemoteProtocolError)


class BencinaClient:
    """Cliente HTTP async para bencinaenlinea.cl con caché TTL por recurso y retry."""

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None
        # { path: (timestamp, data) }
        self._cache: dict[str, tuple[float, Any]] = {}

    def start(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=settings.bencina_base_url,
            timeout=15.0,
            headers={"Accept": "application/json"},
        )
        logger.info("BencinaClient started (base_url=%s)", settings.bencina_base_url)

    async def stop(self) -> None:
        if self._client:
            await self._client.aclose()
            logger.info("BencinaClient closed")

    def clear_cache(self) -> None:
        self._cache.clear()

    async def _fetch(self, path: str) -> Any:
        assert self._client is not None, "Client not started — call start() first"
        async for attempt in AsyncRetrying(
            retry=retry_if_exception_type(_RETRYABLE),
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            reraise=True,
        ):
            with attempt:
                try:
                    response = await self._client.get(path)
                    response.raise_for_status()
                    return response.json()
                except httpx.HTTPStatusError as exc:
                    raise UpstreamError(
                        f"Upstream returned {exc.response.status_code} for {path}"
                    ) from exc
        raise UpstreamError("tenacity debería haber relanzado antes")  # pragma: no cover

    async def _cached_get(self, path: str, ttl: int) -> Any:
        entry = self._cache.get(path)
        if entry:
            ts, data = entry
            if monotonic() - ts < ttl:
                logger.debug("Cache hit: %s", path)
                return data
        logger.debug("Cache miss: %s", path)
        try:
            data = await self._fetch(path)
        except _RETRYABLE as exc:  # type: ignore[misc]
            raise UpstreamError(f"Network error after retries: {exc}") from exc
        self._cache[path] = (monotonic(), data)
        return data

    async def get_stations(self) -> list[dict]:
        data = await self._cached_get("/busqueda_estacion_filtro", settings.station_cache_ttl)
        return data.get("data", [])

    async def get_combustibles(self) -> list[dict]:
        data = await self._cached_get("/combustible_ciudadano", settings.catalog_cache_ttl)
        return data.get("data", [])

    async def get_marcas(self) -> list[dict]:
        data = await self._cached_get("/marca_ciudadano", settings.catalog_cache_ttl)
        return data.get("data", [])

    async def get_servicios(self) -> list[dict]:
        data = await self._cached_get("/servicio_ciudadano", settings.catalog_cache_ttl)
        return data.get("data", [])


bencina_client = BencinaClient()
