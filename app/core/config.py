from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bencina_base_url: str = "https://api.bencinaenlinea.cl/api"
    station_cache_ttl: int = 60
    catalog_cache_ttl: int = 3600
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
