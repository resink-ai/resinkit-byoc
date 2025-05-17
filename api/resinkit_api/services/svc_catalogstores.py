import time
from typing import List, Dict, Any
from flink_gateway_api import Client as FlinkGatewayClient
from resinkit_api.clients.sql_gateway.flink_session import FlinkSession
from resinkit_api.core.flink_options import FlinkOptions
from resinkit_api.api.models.catalogstore import CatalogStoreDefinition
from resinkit_api.core.logging import get_logger

import pandas as pd

logger = get_logger(__name__)


class CatalogStoreService:
    """Service for managing catalog store configurations."""

    def __init__(self, sql_gateway_client: FlinkGatewayClient, refresh_interval_sec: int = 10):
        """Initialize the catalog store service with an empty store."""
        self._sql_gateway_client = sql_gateway_client
        self._catalog_stores: Dict[str, CatalogStoreDefinition] = {}
        self._flink_set_vars: Dict[str, Any] = {}
        self._last_refetch = 0
        self._refresh_interval = refresh_interval_sec

    def _refetch_settings(self):
        """Refresh the catalog stores from the Flink cluster with debounce."""
        if time.time() - self._last_refetch < self._refresh_interval:
            return
        with FlinkSession(self._sql_gateway_client) as session:
            with session.execute("SET;").sync() as operation:
                df_vars: pd.DataFrame = operation.fetch().sync()
                if df_vars is not None:
                    self._flink_set_vars = df_vars.set_index("key")["value"].to_dict()
                    cs_path = FlinkOptions.TABLE_CATALOG_STORE_FILE_PATH.value_of(self._flink_set_vars)
                    cs_kind = FlinkOptions.TABLE_CATALOG_STORE_KIND.value_of(self._flink_set_vars)
                    cs = CatalogStoreDefinition(
                        name="default",
                        kind=cs_kind,
                        options={
                            FlinkOptions.TABLE_CATALOG_STORE_FILE_PATH.key: cs_path,
                            FlinkOptions.TABLE_CATALOG_STORE_KIND.key: cs_kind,
                        },
                    )
                    self._catalog_stores[cs.name] = cs
                    self._last_refetch = time.time()

    async def list(self) -> List[CatalogStoreDefinition]:
        self._refetch_settings()
        return list(self._catalog_stores.values())

    async def get(self, name: str) -> CatalogStoreDefinition:
        self._refetch_settings()
        return self._catalog_stores.get(name)

    async def create(self, store: CatalogStoreDefinition) -> CatalogStoreDefinition:
        raise NotImplementedError("Creating catalog stores is not supported")

    async def delete(self, name: str) -> None:
        raise NotImplementedError("Deleting catalog stores is not supported")
