from typing import List

from pydantic import BaseSettings, Field, validator


class AppSettings(BaseSettings):
	# Runtime context: "local" | "vercel"
	runtime: str = "local"

	# CORS
	enable_cors: bool = False
	cors_origins: List[str] = Field(default_factory=list)

	# Timeouts, cache, rate limit
	rate_limit_rpm: int = 60
	http_timeout: int = 12
	cache_ttl: int = 90
	max_body_kb: int = 128

	# Auth
	auth_mode: str = "none"  # none | apikey | basic | jwt
	api_keys: List[str] = Field(default_factory=list)
	basic_user: str = ""
	basic_password: str = ""
	jwt_public_key: str = ""
	jwt_issuer: str = ""
	jwt_audience: str = ""
	jwt_required_scope: str = ""
	auth_exclude_paths: List[str] = Field(default_factory=lambda: ["/health", "/docs", "/openapi.json"])

	# Misc
	enable_compression: bool = True

	@validator("api_keys", pre=True)
	def _split_api_keys(cls, v):  # type: ignore
		if v is None or v == "":
			return []
		if isinstance(v, list):
			return v
		return [s.strip() for s in str(v).split(",") if s.strip()]

	@validator("cors_origins", pre=True)
	def _split_origins(cls, v):  # type: ignore
		if v is None or v == "":
			return []
		if isinstance(v, list):
			return v
		return [s.strip() for s in str(v).split(",") if s.strip()]

	@validator("auth_exclude_paths", pre=True)
	def _split_excludes(cls, v):  # type: ignore
		if v is None or v == "":
			return ["/health", "/docs", "/openapi.json"]
		if isinstance(v, list):
			return v
		return [s.strip() for s in str(v).split(",") if s.strip()]

	class Config:
		env_file = ".env"
		env_file_encoding = "utf-8"
		case_sensitive = False


