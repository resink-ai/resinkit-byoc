import time
from typing import List, Dict, Any, Optional
from flink_gateway_api import Client as FlinkGatewayClient
from resinkit_api.clients.sql_gateway.flink_session import FlinkSession
from resinkit_api.api.models.catalog import CatalogResponse, CatalogRequest
from resinkit_api.services.svc_catalogstores import CatalogStoreService
from resinkit_api.core.logging import get_logger
from fastapi import HTTPException, status

logger = get_logger(__name__)


class CatalogService:
    """Service for managing catalogs within catalog stores."""

    def __init__(self, sql_gateway_client: FlinkGatewayClient, catalog_store_service: CatalogStoreService, refresh_interval_sec: int = 10):
        """Initialize the catalog service."""
        self._sql_gateway_client = sql_gateway_client
        self._catalog_store_service = catalog_store_service
        self._catalogs: Dict[str, Dict[str, Any]] = {}
        self._last_refetch = 0
        self._refresh_interval = refresh_interval_sec

    def _refetch_catalogs(self, store_name: str):
        """Refresh the catalogs from the Flink cluster with debounce."""
        if time.time() - self._last_refetch < self._refresh_interval:
            return

        with FlinkSession(self._sql_gateway_client) as session:
            with session.execute("SHOW CATALOGS;").sync() as operation:
                result = operation.fetch().sync()
                if result is not None:
                    self._catalogs[store_name] = {}
                    for row in result.itertuples():
                        catalog_name = row[1]  # Assuming the catalog name is in the first column
                        ## Fetch catalog details (currently not supported)
                        # catalog_details = self._fetch_catalog_details(store_name, catalog_name, session) or {}
                        self._catalogs[store_name][catalog_name] = {}
                    self._last_refetch = time.time()

    def _fetch_catalog_details(self, store_name: str, catalog_name: str, session=None) -> Dict[str, Any]:
        """Fetch details for a specific catalog."""
        close_session = False
        if session is None:
            session = FlinkSession(self._sql_gateway_client)
            close_session = True

        try:
            with session.execute(f"DESCRIBE CATALOG {catalog_name};").sync() as operation:
                details = operation.fetch().sync()
                if details is not None:
                    # Convert the details to a dictionary
                    props = {}
                    catalog_type = "jdbc"  # Default type
                    for row in details.itertuples():
                        key, value = row[1], row[2]  # Assuming key and value are in the first two columns
                        if key == "type":
                            catalog_type = value
                        else:
                            props[key] = value

                    if store_name not in self._catalogs:
                        self._catalogs[store_name] = {}

                    return {"name": catalog_name, "type": catalog_type, "properties": props}
        finally:
            if close_session:
                session.close()

    async def list(self, store_name: str) -> List[CatalogResponse]:
        """List all catalogs in the specified catalog store."""
        # Verify the catalog store exists
        store = await self._catalog_store_service.get(store_name)
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "CATALOG_STORE_NOT_FOUND",
                    "message": f"Catalog store '{store_name}' not found",
                    "details": None,
                },
            )

        self._refetch_catalogs(store_name)

        # Return list of catalogs, filtering out sensitive properties
        return [
            {"name": name, "type": info.get("type", "(unknown)"), "properties": {k: v for k, v in info.get("properties", {}).items() if k != "password"}}
            for name, info in self._catalogs.get(store_name, {}).items()
        ]

    async def get(self, store_name: str, catalog_name: str) -> CatalogResponse:
        """Get details for a specific catalog."""
        # Verify the catalog store exists
        store = await self._catalog_store_service.get(store_name)
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "CATALOG_STORE_NOT_FOUND",
                    "message": f"Catalog store '{store_name}' not found",
                    "details": None,
                },
            )

        self._refetch_catalogs(store_name)

        # Check if the catalog exists
        if store_name not in self._catalogs or catalog_name not in self._catalogs.get(store_name, {}):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "CATALOG_NOT_FOUND",
                    "message": f"Catalog '{catalog_name}' not found in store '{store_name}'",
                    "details": None,
                },
            )

        catalog_info = self._catalogs[store_name][catalog_name]
        return {
            "name": catalog_name,
            "type": catalog_info.get("type", "(unknown)"),
            "properties": {k: v for k, v in catalog_info.get("properties", {}).items() if k != "password"},
        }

    async def create(self, store_name: str, catalog: CatalogRequest) -> CatalogResponse:
        """Create a new catalog."""
        # Verify the catalog store exists
        store = await self._catalog_store_service.get(store_name)
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "CATALOG_STORE_NOT_FOUND",
                    "message": f"Catalog store '{store_name}' not found",
                    "details": None,
                },
            )

        self._refetch_catalogs(store_name)

        # Check if the catalog already exists
        if store_name in self._catalogs and catalog.name in self._catalogs.get(store_name, {}):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error_code": "CATALOG_ALREADY_EXISTS",
                    "message": f"Catalog '{catalog.name}' already exists in store '{store_name}'",
                    "details": None,
                },
            )

        # Generate the SQL for creating the catalog
        create_catalog_sql = self._generate_create_catalog_sql(catalog)

        # Execute the SQL to create the catalog
        with FlinkSession(self._sql_gateway_client) as session:
            try:
                with session.execute(create_catalog_sql).sync() as operation:
                    operation.fetch().sync()
                    # Force a refetch of catalogs after creation
                    self._last_refetch = 0
                    self._refetch_catalogs(store_name)

                    # Return the created catalog details
                    return {"name": catalog.name, "type": catalog.type, "properties": {k: v for k, v in catalog.properties.items() if k != "password"}}
            except Exception as e:
                logger.error(f"Error creating catalog: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "error_code": "INTERNAL_SERVER_ERROR",
                        "message": "An error occurred while creating the catalog",
                        "details": str(e),
                    },
                )

    async def update(self, store_name: str, catalog_name: str, catalog: CatalogRequest) -> CatalogResponse:
        """Update an existing catalog."""
        # Verify the catalog store exists
        store = await self._catalog_store_service.get(store_name)
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "CATALOG_STORE_NOT_FOUND",
                    "message": f"Catalog store '{store_name}' not found",
                    "details": None,
                },
            )

        # Verify the catalog name matches
        if catalog.name != catalog_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "INVALID_REQUEST",
                    "message": "Catalog name in the URL does not match the name in the request body",
                    "details": None,
                },
            )

        self._refetch_catalogs(store_name)

        # Check if the catalog exists
        if store_name not in self._catalogs or catalog_name not in self._catalogs.get(store_name, {}):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "CATALOG_NOT_FOUND",
                    "message": f"Catalog '{catalog_name}' not found in store '{store_name}'",
                    "details": None,
                },
            )

        # For update, we'll drop and recreate the catalog
        await self.delete(store_name, catalog_name)
        return await self.create(store_name, catalog)

    async def delete(self, store_name: str, catalog_name: str) -> None:
        """Delete a catalog."""
        # Verify the catalog store exists
        store = await self._catalog_store_service.get(store_name)
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "CATALOG_STORE_NOT_FOUND",
                    "message": f"Catalog store '{store_name}' not found",
                    "details": None,
                },
            )

        self._refetch_catalogs(store_name)

        # Check if the catalog exists
        if store_name not in self._catalogs or catalog_name not in self._catalogs.get(store_name, {}):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "CATALOG_NOT_FOUND",
                    "message": f"Catalog '{catalog_name}' not found in store '{store_name}'",
                    "details": None,
                },
            )

        # Execute SQL to drop the catalog
        with FlinkSession(self._sql_gateway_client) as session:
            try:
                # Drop the catalog
                with session.execute(f"DROP CATALOG {catalog_name};").sync() as operation:
                    operation.fetch().sync()
                    # Remove from our local cache
                    if store_name in self._catalogs and catalog_name in self._catalogs[store_name]:
                        del self._catalogs[store_name][catalog_name]
                    # Force a refetch of catalogs after deletion
                    self._last_refetch = 0
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error deleting catalog: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "error_code": "INTERNAL_SERVER_ERROR",
                        "message": "An error occurred while deleting the catalog",
                        "details": str(e),
                    },
                )

    def _generate_create_catalog_sql(self, catalog: CatalogRequest) -> str:
        """Generate SQL for creating a catalog.

        Example:
        CREATE CATALOG hive WITH (
            'type' = 'hive',
            'hive.metastore.uris' = 'thrift://localhost:9083'
        );
        """
        properties_sql = ", ".join([f"'{k}' = '{v}'" for k, v in catalog.properties.items()])

        return f"""
        CREATE CATALOG {catalog.name} WITH (
            'type' = '{catalog.type}',
            {properties_sql}
        );
        """
