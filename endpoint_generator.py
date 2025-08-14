from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from cache_manager import cache_manager
from data_store import get_data
from logger import log_api_request


class EndpointGenerator:
    """Generate endpoints dynamically to eliminate code duplication"""

    def __init__(self):
        self.router = APIRouter()
        self.setup_endpoints()

    def setup_endpoints(self):
        """Setup all dynamic endpoints"""

        # Endpoints by data type
        data_types = {
            "indices": ["tradingview", "finviz", "yahoo"],
            "acciones": ["tradingview", "finviz", "yahoo"],
            "cripto": ["tradingview"],
            "forex": ["tradingview", "finviz", "yahoo"],
            "etfs": ["yahoo"],
            "materias-primas": ["yahoo"],
        }

        # Create endpoints for each data type
        for data_type, sources in data_types.items():
            self.create_data_type_endpoint(data_type, sources)

        # Endpoints by source
        sources = {
            "tradingview": ["indices", "acciones", "cripto", "forex"],
            "finviz": ["indices", "acciones", "forex"],
            "yahoo": [
                "indices",
                "acciones",
                "forex",
                "etfs",
                "materias-primas",
                "gainers",
                "losers",
                "most-active",
                "undervalued",
            ],
        }

        # Create endpoints for each source
        for source, data_types in sources.items():
            self.create_source_endpoint(source, data_types)

        # Create specific endpoints for source + data type combinations
        for source, data_types in sources.items():
            for data_type in data_types:
                self.create_specific_endpoint(source, data_type)

    def create_data_type_endpoint(self, data_type: str, sources: List[str]):
        """Create endpoint for a specific data type across all sources"""

        @self.router.get(f"/datos/{data_type}")
        async def get_data_type_endpoint():
            log_api_request("GET", f"/datos/{data_type}")

            # Check cache first
            cache_key = f"data_type_{data_type}"
            cached_data = cache_manager.get(cache_key)
            if cached_data:
                return JSONResponse(content=cached_data, status_code=200)

            try:
                data = get_data()
                result = {"last_updated": data.get("last_updated")}

                # Add data from each source
                for source in sources:
                    source_data = data.get(source, {})
                    if data_type in source_data:
                        result[source] = source_data[data_type]
                    elif data_type == "acciones" and source == "yahoo":
                        # Special case for Yahoo actions
                        result[source] = {
                            "gainers": source_data.get("gainers", []),
                            "losers": source_data.get("losers", []),
                            "most_active_stocks": source_data.get("most_active_stocks", []),
                        }

                # Cache the result
                cache_manager.set(cache_key, result)

                return JSONResponse(content=result, status_code=200)

            except Exception as e:
                raise HTTPException(status_code=500, detail="Error interno del servidor")

    def create_source_endpoint(self, source: str, data_types: List[str]):
        """Create endpoint for a specific source"""

        @self.router.get(f"/datos/{source}")
        async def get_source_endpoint():
            log_api_request("GET", f"/datos/{source}")

            # Check cache first
            cache_key = f"source_{source}"
            cached_data = cache_manager.get(cache_key)
            if cached_data:
                return JSONResponse(content=cached_data, status_code=200)

            try:
                data = get_data()
                source_data = data.get(source, {})
                result = {"last_updated": data.get("last_updated")}

                # Add all data types for this source
                for data_type in data_types:
                    if data_type in source_data:
                        result[data_type] = source_data[data_type]

                # Cache the result
                cache_manager.set(cache_key, result)

                return JSONResponse(content=result, status_code=200)

            except Exception as e:
                raise HTTPException(status_code=500, detail="Error interno del servidor")

    def create_specific_endpoint(self, source: str, data_type: str):
        """Create endpoint for specific source + data type combination"""

        @self.router.get(f"/datos/{source}/{data_type}")
        async def get_specific_endpoint():
            log_api_request("GET", f"/datos/{source}/{data_type}")

            # Check cache first
            cache_key = f"specific_{source}_{data_type}"
            cached_data = cache_manager.get(cache_key)
            if cached_data:
                return JSONResponse(content=cached_data, status_code=200)

            try:
                data = get_data()
                source_data = data.get(source, {})

                if data_type in source_data:
                    result = {data_type: source_data[data_type], "last_updated": data.get("last_updated")}
                else:
                    result = {data_type: [], "last_updated": data.get("last_updated")}

                # Cache the result
                cache_manager.set(cache_key, result)

                return JSONResponse(content=result, status_code=200)

            except Exception as e:
                raise HTTPException(status_code=500, detail="Error interno del servidor")


# Create global endpoint generator
endpoint_generator = EndpointGenerator()
