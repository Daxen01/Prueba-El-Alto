import asyncio
import logging
from typing import Any

from app.clients.bencina import bencina_client
from app.core.exceptions import NoStationsFoundError, ProductNotFoundError
from app.core.geo import haversine
from app.schemas.query import ProductEnum

logger = logging.getLogger(__name__)

# producto → nombre_corto en la API (incluye variante autoservicio)
_PRODUCT_SHORT_NAMES: dict[str, list[str]] = {
    ProductEnum.gasolina_93: ["93", "A93"],
    ProductEnum.gasolina_95: ["95", "A95"],
    ProductEnum.gasolina_97: ["97", "A97"],
    ProductEnum.diesel: ["DI", "ADI"],
    ProductEnum.kerosene: ["KE", "AKE"],
}

# campo precio en la respuesta para cada producto
_PRICE_FIELD: dict[str, str] = {
    ProductEnum.gasolina_93: "precios93",
    ProductEnum.gasolina_95: "precios95",
    ProductEnum.gasolina_97: "precios97",
    ProductEnum.diesel: "preciosDiesel",
    ProductEnum.kerosene: "preciosKerosene",
}

# id=4 en el catálogo servicio_ciudadano
_TIENDA_SERVICE_ID = 4


def _get_product_price(station: dict, short_names: list[str]) -> int | None:
    """Lowest valid price for the product at this station, or None if unavailable."""
    prices = [
        int(float(c["precio"]))
        for c in station.get("combustibles", [])
        if c.get("nombre_corto") in short_names
        and c.get("precio")
        and float(c["precio"]) > 0
    ]
    return min(prices) if prices else None


def _has_tienda(station: dict) -> bool:
    # Primero busca id=4; si no hay ids, servicios no vacío sirve de fallback
    # (la API puede tener registros con id/nombre nulos)
    servicios = station.get("servicios", [])
    if any(s.get("id") == _TIENDA_SERVICE_ID for s in servicios):
        return True
    return len(servicios) > 0


async def search_station(
    lat: float,
    lng: float,
    product: ProductEnum,
    nearest: bool = True,
    store: bool = False,
    cheapest: bool = False,
) -> dict[str, Any]:
    """Retorna la estación que mejor cumple los criterios de búsqueda."""
    short_names = _PRODUCT_SHORT_NAMES[product]
    price_field = _PRICE_FIELD[product]

    # fetch en paralelo; servicios solo calienta el caché (tienda viene en station.servicios)
    stations, marcas_list, _ = await asyncio.gather(
        bencina_client.get_stations(),
        bencina_client.get_marcas(),
        bencina_client.get_servicios(),
    )

    marca_lookup: dict[int, str] = {m["id"]: m["nombre"] for m in marcas_list}

    # descartar estaciones sin precio válido para el producto
    candidates: list[dict] = []
    for s in stations:
        price = _get_product_price(s, short_names)
        if price is not None:
            candidates.append({**s, "_price": price})

    if not candidates:
        raise ProductNotFoundError(
            f"No hay estaciones que vendan '{product.value}' con precio disponible."
        )

    # filtrar por tienda si se pidió
    if store:
        candidates = [s for s in candidates if _has_tienda(s)]
        if not candidates:
            raise NoStationsFoundError(
                f"No se encontraron estaciones con tienda para '{product.value}'."
            )

    # solo el precio mínimo del subconjunto actual
    if cheapest:
        min_price = min(s["_price"] for s in candidates)
        candidates = [s for s in candidates if s["_price"] == min_price]

    # calcular distancia y elegir el más cercano
    for s in candidates:
        # la API puede usar coma como separador decimal
        lat_str = s["latitud"].replace(',', '.')
        lng_str = s["longitud"].replace(',', '.')
        s["_distance_km"] = haversine(lat, lng, float(lat_str), float(lng_str))

    best = min(candidates, key=lambda s: s["_distance_km"])

    tiene_tienda = _has_tienda(best)
    tienda = {"presente": True} if tiene_tienda else None

    return {
        "success": True,
        "data": {
            "id": str(best["id"]),
            "compania": marca_lookup.get(best["marca"], f"Marca {best['marca']}"),
            "direccion": best["direccion"].strip(),
            "comuna": best["comuna"],
            "region": best["region"],
            "latitud": float(best["latitud"].replace(',', '.')),
            "longitud": float(best["longitud"].replace(',', '.')),
            "distancia(lineal)": round(best["_distance_km"], 3),
            price_field: best["_price"],
            "tiene_tienda": tiene_tienda,
            "tienda": tienda,
        },
    }
