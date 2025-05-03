from resinkit_api.services.svc_catalog import CatalogService
from resinkit_api.services.svc_catalogstores import CatalogStoreService
from resinkit_api.core.logging import get_logger
from resinkit_api.core.config import settings
from flink_gateway_api import Client as FlinkGatewayClient

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
        self._svc_catalog_store: "CatalogStoreService" = CatalogStoreService(
            self._sql_gateway_client
        )
        self._svc_catalog: "CatalogService" = CatalogService(
            self._sql_gateway_client,
            self._svc_catalog_store
        )

    @property
    def catalogstore(self) -> "CatalogStoreService":
        return self._svc_catalog_store

    @property
    def catalog(self) -> "CatalogService":
        return self._svc_catalog

service_manager = SvcManager()
