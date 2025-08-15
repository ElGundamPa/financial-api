import os
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class AppSettings(BaseModel):
    """
    Configuración de la aplicación, cargada desde variables de entorno o .env.
    Compatible con Pydantic v2.
    """

    runtime: str = Field("local", description="Entorno de ejecución (local, vercel)")

    # CORS
    enable_cors: bool = Field(False, description="Habilitar CORS")
    cors_origins: List[str] = Field(default_factory=list, description="Orígenes CORS permitidos")

    # Rate Limiting
    rate_limit_rpm: int = Field(60, description="Límite de peticiones por minuto")

    # HTTP Client
    http_timeout: int = Field(12, description="Timeout para peticiones HTTP externas")

    # Cache
    cache_ttl: int = Field(90, description="TTL de la caché en segundos")

    # Request Body Limits
    max_body_kb: int = Field(128, description="Tamaño máximo del body de la petición en KB")

    # Logging
    log_level: str = Field("INFO", description="Nivel de logging")

    # Authentication
    auth_mode: str = Field("none", description="Modo de autenticación (none, apikey, basic, jwt)")
    api_keys: List[str] = Field(default_factory=list, description="API Keys permitidas")
    basic_user: str = Field("", description="Usuario para Basic Auth")
    basic_password: str = Field("", description="Contraseña para Basic Auth")
    jwt_public_key: str = Field("", description="Clave pública para JWT (RS256)")
    jwt_issuer: str = Field("", description="Issuer esperado para JWT")
    jwt_audience: str = Field("", description="Audience esperado para JWT")
    jwt_required_scope: str = Field("", description="Scope requerido para JWT")
    auth_exclude_paths: List[str] = Field(
        default_factory=lambda: ["/health", "/docs", "/openapi.json"],
        description="Rutas excluidas de autenticación"
    )

    @field_validator("api_keys", mode="before")
    @classmethod
    def _split_api_keys(cls, v):
        if v is None or v == "":
            return []
        if isinstance(v, list):
            return v
        return [s.strip() for s in str(v).split(",") if s.strip()]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, v):
        if v is None or v == "":
            return []
        if isinstance(v, list):
            return v
        return [s.strip() for s in str(v).split(",") if s.strip()]

    @field_validator("auth_exclude_paths", mode="before")
    @classmethod
    def _split_excludes(cls, v):
        if v is None or v == "":
            return ["/health", "/docs", "/openapi.json"]
        if isinstance(v, list):
            return v
        return [s.strip() for s in str(v).split(",") if s.strip()]

    @classmethod
    def from_env(cls, runtime: str = "local"):
        """Cargar configuración desde variables de entorno"""
        # Cargar .env si existe (solo en local)
        if runtime == "local":
            try:
                from dotenv import load_dotenv
                load_dotenv()
            except ImportError:
                pass

        # Crear instancia con valores por defecto
        settings = cls(runtime=runtime)

        # Override con variables de entorno
        if os.getenv("AUTH_MODE"):
            settings.auth_mode = os.getenv("AUTH_MODE", "none").lower()
        if os.getenv("API_KEYS"):
            settings.api_keys = [k.strip() for k in os.getenv("API_KEYS", "").split(",") if k.strip()]
        if os.getenv("BASIC_USER"):
            settings.basic_user = os.getenv("BASIC_USER", "")
        if os.getenv("BASIC_PASSWORD"):
            settings.basic_password = os.getenv("BASIC_PASSWORD", "")
        if os.getenv("JWT_PUBLIC_KEY"):
            settings.jwt_public_key = os.getenv("JWT_PUBLIC_KEY", "")
        if os.getenv("JWT_ISSUER"):
            settings.jwt_issuer = os.getenv("JWT_ISSUER", "")
        if os.getenv("JWT_AUDIENCE"):
            settings.jwt_audience = os.getenv("JWT_AUDIENCE", "")
        if os.getenv("JWT_REQUIRED_SCOPE"):
            settings.jwt_required_scope = os.getenv("JWT_REQUIRED_SCOPE", "")
        if os.getenv("ENABLE_CORS"):
            settings.enable_cors = os.getenv("ENABLE_CORS", "false").lower() == "true"
        if os.getenv("CORS_ORIGINS"):
            settings.cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
        if os.getenv("RATE_LIMIT_RPM"):
            settings.rate_limit_rpm = int(os.getenv("RATE_LIMIT_RPM", "60"))
        if os.getenv("HTTP_TIMEOUT_SECONDS"):
            settings.http_timeout = int(os.getenv("HTTP_TIMEOUT_SECONDS", "12"))
        if os.getenv("CACHE_TTL_SECONDS"):
            settings.cache_ttl = int(os.getenv("CACHE_TTL_SECONDS", "90"))
        if os.getenv("MAX_BODY_KB"):
            settings.max_body_kb = int(os.getenv("MAX_BODY_KB", "128"))
        if os.getenv("LOG_LEVEL"):
            settings.log_level = os.getenv("LOG_LEVEL", "INFO")

        return settings


