from typing import Optional

from flink_gateway_api import Client

from resinkit_api.clients.sql_gateway.flink_session import FlinkSession
from resinkit_api.core.config import settings
from resinkit_api.core.logging import get_logger

logger = get_logger(__name__)


class FlinkSqlGatewayClient:
    """Client for managing calls to Flink SQL Gateway REST endpoint."""

    def __init__(self, gateway_url: Optional[str] = None):
        """Initialize the Flink SQL Gateway client.

        Args:
            gateway_url: The URL of the Flink SQL Gateway. If not provided,
                         it will use the URL from the settings.
        """
        self.gateway_url = gateway_url or settings.FLINK_SQL_GATEWAY_URL
        logger.info(f"Initializing Flink SQL Gateway client with URL: {self.gateway_url}")
        self.client = Client(base_url=self.gateway_url)

    def get_client(self) -> Client:
        return self.client

    def get_session(
        self, 
        properties: Optional[dict] = None, 
        session_name: Optional[str] = None
    ) -> FlinkSession:
        """Get a Flink session instance.

        Args:
            properties: Session properties.
            session_name: Name of the session.

        Returns:
            FlinkSession: A session instance for the Flink SQL Gateway.
        """
        client = self.get_client()
        return FlinkSession(client, properties, session_name)
