# API Bencina en Línea

API REST construida con **FastAPI** para buscar estaciones de combustible por ubicación geográfica, consumiendo datos en tiempo real desde [bencinaenlinea.cl](https://bencinaenlinea.cl).

---

## Tabla de contenidos

1. [Arquitectura](#arquitectura)
2. [Tech Stack](#tech-stack)
3. [Instalación y ejecución](#instalación-y-ejecución)
4. [Endpoints](#endpoints)
5. [Los 4 casos de búsqueda](#los-4-casos-de-búsqueda)
6. [Ejemplos con curl](#ejemplos-con-curl)
7. [Tests](#tests)
8. [Decisiones técnicas](#decisiones-técnicas)

---

## Arquitectura

```
app/
├── main.py                  # FastAPI + lifespan + exception handlers
├── core/
│   ├── config.py            # pydantic-settings (variables de entorno)
│   ├── exceptions.py        # Jerarquía de errores + handlers globales
│   └── geo.py               # Fórmula haversine (distancia great-circle)
├── schemas/
│   ├── query.py             # Validación de parámetros de entrada (Pydantic v2)
│   └── response.py          # Modelos de respuesta
├── clients/
│   └── bencina.py           # AsyncClient httpx + cache TTL + retry tenacity
├── services/
│   └── station_search.py    # Lógica de negocio (filtrado y ranking)
└── routers/
    └── stations.py          # Endpoint GET /api/stations/search

tests/
├── conftest.py              # Fixtures + mock data (respx + AsyncMock)
├── test_geo.py              # Tests unitarios de haversine
├── test_service.py          # Tests unitarios del servicio (4 casos + errores)
└── test_routes.py           # Tests de integración con TestClient

docs/
└── postman_collection.json  # Colección importable con los 4 casos
```

---

## Tech Stack

| Componente | Librería |
|---|---|
| Framework API | FastAPI 0.111+ |
| Servidor ASGI | Uvicorn |
| HTTP async | httpx (AsyncClient) |
| Validación | Pydantic v2 |
| Config | pydantic-settings |
| Retry | tenacity |
| Tests | pytest + pytest-asyncio + respx |
| Linter | ruff |

---

## Instalación y ejecución

### Requisitos

- Python 3.11+

### Pasos

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd bencina-api

# 2. Crear y activar entorno virtual
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# 3. Instalar dependencias
pip install -e ".[dev]"

# 4. (Opcional) Configurar variables de entorno
cp .env.example .env
# editar .env según necesidad

# 5. Levantar el servidor
uvicorn app.main:app --reload
```

La API queda disponible en `http://localhost:8000`.

La documentación interactiva (Swagger UI) en `http://localhost:8000/docs`.

---

## Endpoints

### `GET /health`

Verifica que la API esté en línea.

```json
{ "status": "ok", "service": "bencina-api", "version": "1.0.0" }
```

### `GET /api/stations/search`

Busca la estación de combustible que mejor cumple los criterios.

**Parámetros:**

| Parámetro | Tipo | Requerido | Descripción |
|---|---|---|---|
| `lat` | float | sí | Latitud [-90, 90] |
| `lng` | float | sí | Longitud [-180, 180] |
| `product` | string | sí | `93`, `95`, `97`, `diesel`, `kerosene` |
| `nearest` | bool | no | Ordenar por cercanía (default: `true`) |
| `store` | bool | no | Solo estaciones con tienda (default: `false`) |
| `cheapest` | bool | no | Solo las de menor precio (default: `false`) |

**Respuesta exitosa:**

```json
{
  "success": true,
  "data": {
    "id": "29",
    "compania": "COPEC",
    "direccion": "San Martin Esq. Uribe",
    "comuna": "Antofagasta",
    "region": "Antofagasta",
    "latitud": -23.6491868026,
    "longitud": -70.4011811037,
    "distancia(lineal)": 0.523,
    "precios93": 1657,
    "tiene_tienda": true,
    "tienda": { "presente": true }
  }
}
```

**Respuesta de error:**

```json
{
  "success": false,
  "error": {
    "code": "PRODUCT_NOT_FOUND",
    "message": "No hay estaciones que vendan 'kerosene' con precio disponible."
  }
}
```

---

## Los 4 casos de búsqueda

| # | Descripción | Flags |
|---|---|---|
| 1 | Estación más cercana por producto | `nearest=true` (default) |
| 2 | Estación más cercana con menor precio | `cheapest=true` |
| 3 | Estación más cercana con tienda | `store=true` |
| 4 | Estación más cercana con tienda y menor precio | `store=true&cheapest=true` |

**Algoritmo (pipeline funcional en `services/station_search.py`):**

```
1. Filtrar estaciones que tienen el producto con precio > 0
2. Si store=true  → filtrar por tienda (service id=4 en el catálogo)
3. Si cheapest=true → filtrar al precio mínimo del subconjunto actual
4. Calcular distancia haversine a cada candidato
5. Retornar el de menor distancia
```

---

## Ejemplos con curl

Coordenadas de ejemplo: centro de Antofagasta (`lat=-23.65, lng=-70.40`)

```bash
# Caso 1: estación más cercana con Gasolina 93
curl "http://localhost:8000/api/stations/search?lat=-23.65&lng=-70.40&product=93"

# Caso 2: más cercana entre las más baratas (Gasolina 95)
curl "http://localhost:8000/api/stations/search?lat=-23.65&lng=-70.40&product=95&cheapest=true"

# Caso 3: más cercana con tienda (Diesel)
curl "http://localhost:8000/api/stations/search?lat=-23.65&lng=-70.40&product=diesel&store=true"

# Caso 4: más cercana con tienda y menor precio (Gasolina 97)
curl "http://localhost:8000/api/stations/search?lat=-23.65&lng=-70.40&product=97&store=true&cheapest=true"
```

La colección Postman con todos los casos está en `docs/postman_collection.json`. Importarla directamente en Postman con _File → Import_.

---

## Tests

```bash
# Ejecutar todos los tests
pytest -v

# Con reporte de cobertura
pytest --cov=app --cov-report=term-missing

# Solo tests unitarios (sin red)
pytest tests/test_geo.py tests/test_service.py -v
```

**Cobertura por capa:**

| Archivo de test | Qué prueba |
|---|---|
| `test_geo.py` | Fórmula haversine (5 casos: punto igual, simetría, distancia conocida, ecuador, tipo) |
| `test_service.py` | Los 4 casos de búsqueda + validación estructura + 2 errores (ProductNotFound, NoStationsFound) |
| `test_routes.py` | HTTP 200 (4 casos), 422 (3 validaciones), 404 (producto no disponible), 502 (upstream caído) |

---

## Decisiones técnicas

### ¿Por qué solo 3 de los 4 endpoints upstream?

| Endpoint | Razón |
|---|---|
| `busqueda_estacion_filtro` | Fuente principal de datos |
| `combustible_ciudadano` | Catálogo dinámico de productos (la API devuelve `nombre_corto` en combustibles) |
| `servicio_ciudadano` | Calienta el caché; la detección de tienda se hace por `id=4` en `station.servicios[]` |
| `marca_ciudadano` | La API devuelve `marca` como int (id), no como string; necesario para obtener el nombre de la compañía |

### ¿Por qué TTL diferenciado?

Los catálogos (`combustible`, `marca`, `servicio`) cambian rara vez → TTL 1 hora.  
Los precios de estaciones pueden actualizarse durante el día → TTL 60 segundos.  
Esto reduce llamadas al upstream en ~99% en condiciones normales de uso.

### ¿Por qué haversine propio en lugar de `geopy`?

La fórmula haversine son 8 líneas de Python estándar y es completamente testeada.  
Agregar `geopy` como dependencia por eso sería sobre-ingenierizado.

### ¿Por qué no usar `cachetools`?

`cachetools.TTLCache` no es async-safe sin un lock adicional.  
Un dict Python con timestamp es atómico bajo el GIL en un proceso único y cero dependencias extra.

### ¿Por qué `tenacity` con `AsyncRetrying`?

`@retry` de tenacity sobre métodos de instancia puede no enlazarse correctamente como bound method.  
`AsyncRetrying` como context manager es más explícito, sin ambigüedad y 100% predecible.

### Próximos pasos para producción

- [ ] Dockerfile + docker-compose
- [ ] GitHub Actions CI (ruff + pytest + cobertura)
- [ ] Rate limiting con `slowapi`
- [ ] Redis para caché distribuida (múltiples workers)
- [ ] Logging estructurado JSON con request-id
