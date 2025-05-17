from resinkit_api.services.svc_catalog import CatalogService
from resinkit_api.services.svc_catalogstores import CatalogStoreService
from resinkit_api.core.logging import get_logger
from resinkit_api.core.config import settings
from flink_gateway_api import Client as FlinkGatewayClient
from resinkit_api.clients.job_manager.flink_job_manager_client import FlinkJobManager
from resinkit_api.clients.sql_gateway.flink_sql_gateway_client import FlinkSqlGatewayClient

logger = get_logger(__name__)


class SvcManager:
    """
    Service manager responsible for creating and managing service instances.
    This provides a central point of access to all services with dependency injection.
    """

    def __init__(self):
        """
        Initialize the service manager with dependencies.

        Args:
            flink_gateway_api_client: Client for Flink Gateway API (if needed).
        """
        logger.debug("Initializing service manager")

        self._sql_gateway_client = FlinkGatewayClient(
            base_url=settings.FLINK_SQL_GATEWAY_URL,
            raise_on_unexpected_status=True,
        )

        # Initialize services
        self._svc_catalog_store: "CatalogStoreService" = CatalogStoreService(self._sql_gateway_client)
        self._svc_catalog: "CatalogService" = CatalogService(self._sql_gateway_client, self._svc_catalog_store)

        self._job_manager_client: "FlinkJobManager" = FlinkJobManager()
        self._sql_gateway_client: "FlinkSqlGatewayClient" = FlinkSqlGatewayClient()

    @property
    def catalogstore(self) -> "CatalogStoreService":
        return self._svc_catalog_store

    @property
    def catalog(self) -> "CatalogService":
        return self._svc_catalog

    @property
    def job_manager(self) -> "FlinkJobManager":
        return self._job_manager_client

    @property
    def sql_gateway(self) -> "FlinkSqlGatewayClient":
        return self._sql_gateway_client
