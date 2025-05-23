import uuid
from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncGenerator, Dict, Generator, List, Optional

from flink_gateway_api import Client
from flink_gateway_api.api.default import (
    close_session,
    complete_statement,
    execute_statement,
    open_session,
    trigger_session,
    get_operation_status,
)
from flink_gateway_api.models import (
    CompleteStatementRequestBody,
    CompleteStatementResponseBody,
    ExecuteStatementRequestBody,
    OpenSessionRequestBody,
    OperationStatusResponseBody,
)


from resinkit_api.clients.sql_gateway.flink_operation import FlinkCompositeOperation, FlinkOperation
from resinkit_api.clients.sql_gateway.session_utils import (
    get_execute_statement_request,
)

from resinkit_api.core.logging import get_logger

logger = get_logger(__name__)


class FlinkSession:
    """A context manager for managing a Flink session.

    Examples:
    ```python
        with FlinkSession(fg_client) as session:
        with session.execute(sql_t0).sync() as operation:
            df = operation.fetch().sync()
    ```

    # TODO: support open session with TTL
    """

    def __init__(self, client: Client, properties: Dict[str, str] = None, session_name: str = None, create_if_not_exist: bool = True):
        self.properties = properties or {}
        self.session_handle: Optional[str] = None
        self.session_name = session_name or f"session_{uuid.uuid4()}"
        self.client: Client = client
        self.was_alive = False  # Whether the session was alive when last checked
        self.create_if_not_exist = create_if_not_exist

    async def __aenter__(self):
        await self.open_async()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.try_close_async()

    def __enter__(self):
        self.open_sync()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.try_close_sync()

    def open_sync(self):
        # If create_if_not_exist is False, do nothing
        if not self.create_if_not_exist:
            return
        # If session is alive, do nothing
        if self.is_alive():
            return
        # Otherwise, open a new session
        response = open_session.sync(
            client=self.client, body=OpenSessionRequestBody.from_dict({"properties": self.properties, "sessionName": self.session_name})
        )
        self.session_handle = response.session_handle
        self.was_alive = True

    async def open_async(self):
        # If create_if_not_exist is False, do nothing
        if not self.create_if_not_exist:
            return
        # If session is alive, do nothing
        if self.is_alive():
            return
        # Otherwise, open a new session
        response = await open_session.asyncio(
            client=self.client, body=OpenSessionRequestBody.from_dict({"properties": self.properties, "sessionName": self.session_name})
        )
        self.session_handle = response.session_handle
        self.was_alive = True

    def try_close_sync(self):
        if not self.session_handle:
            return
        try:
            close_session.sync(self.session_handle, client=self.client)
        except Exception as e:
            logger.warning(f"Failed to close session {self.session_name}: {str(e)}")

    async def try_close_async(self):
        if not self.session_handle:
            return
        try:
            await close_session.asyncio(self.session_handle, client=self.client)
        except Exception as e:
            logger.warning(f"Failed to close session {self.session_name}: {str(e)}")

    def complete_statement(self) -> "SessionCompleteStatement":
        return SessionCompleteStatement(self)

    def execute(self, sql: str, query_props: Optional[Dict[str, Any]] = None, execute_timeout: Optional[int] = None) -> "ExecuteDispatch":
        """Execute a SQL statement in a single session.
        Args:
            sql: SQL statement to execute
            query_props: executionConfig
            execute_timeout: executionTimeout

        Returns: a dispatch, results of which can be fetched synchronously or asynchronously
        """
        return ExecuteDispatch(self, sql, query_props, execute_timeout)

    def execute_all(self, sqls: List[str], query_props: Optional[Dict[str, Any]] = None, execute_timeout: Optional[int] = None) -> "ExecuteAllDispatch":
        """Execute multiple SQL statements concurrently in a single session.

        Args:
            sqls: List of SQL statements to execute
            query_props: executionConfig
            execute_timeout: executionTimeout

        Returns: a dispatch, results of which can be fetched synchronously or asynchronously
        """
        return ExecuteAllDispatch(self, sqls, query_props, execute_timeout)

    def trigger_heartbeat(self):
        return trigger_session.sync_detailed(session_handle=self.session_handle, client=self.client)

    def is_alive(self):
        if not self.session_handle:
            return False
        try:
            response = self.client.get_httpx_client().request(
                method="POST",
                url=f"/sessions/{self.session_handle}/heartbeat",
            )
            self.was_alive = response.status_code == 200
            return self.was_alive
        except Exception:
            self.was_alive = False
            return False

    @staticmethod
    def get_operation_status(
        client: Client,
        session_handle: str,
        operation_handle: str,
    ) -> Optional[str]:
        response: OperationStatusResponseBody = get_operation_status.sync(session_handle=session_handle, operation_handle=operation_handle, client=client)
        return response.status


class SessionCompleteStatement:
    def __init__(self, session: FlinkSession):
        self.session = session

    def sync(self, position: int, statement: str) -> CompleteStatementResponseBody:
        return complete_statement.sync(
            self.session.session_handle,
            client=self.session.client,
            body=CompleteStatementRequestBody.from_dict(
                {
                    "position": position,
                    "statement": statement,
                }
            ),
        )

    async def asyncio(self, position: int, statement: str) -> CompleteStatementResponseBody:
        return await complete_statement.asyncio(
            self.session.session_handle,
            client=self.session.client,
            body=CompleteStatementRequestBody.from_dict(
                {
                    "position": position,
                    "statement": statement,
                }
            ),
        )


class ExecuteDispatch:
    def __init__(self, session: "FlinkSession", sql: str, query_props=None, execute_timeout=None):
        self.session = session
        self.sql = sql
        self.query_props = query_props
        self.execute_timeout = execute_timeout

    @contextmanager
    def sync(self) -> Generator[FlinkOperation, None, None]:
        request_dict = get_execute_statement_request(self.sql, self.query_props, self.execute_timeout)
        response = execute_statement.sync(self.session.session_handle, client=self.session.client, body=ExecuteStatementRequestBody.from_dict(request_dict))
        operation = FlinkOperation(self.session, response.operation_handle)
        try:
            yield operation
        finally:
            operation.close().sync()

    @asynccontextmanager
    async def asyncio(self) -> AsyncGenerator[FlinkOperation, None]:
        request_dict = get_execute_statement_request(self.sql, self.query_props, self.execute_timeout)
        response = await execute_statement.asyncio(
            self.session.session_handle, client=self.session.client, body=ExecuteStatementRequestBody.from_dict(request_dict)
        )
        operation = FlinkOperation(self.session, response.operation_handle)
        try:
            yield operation
        finally:
            await operation.close().asyncio()


class ExecuteAllDispatch:
    def __init__(self, session: "FlinkSession", sqls: List[str], query_props=None, execute_timeout=None):
        self.session = session
        self.sqls = sqls
        self.query_props = query_props
        self.execute_timeout = execute_timeout

    @contextmanager
    def sync(self) -> Generator[FlinkCompositeOperation, None, None]:
        operations = []
        for sql in self.sqls:
            request_dict = get_execute_statement_request(sql, self.query_props, self.execute_timeout)
            response = execute_statement.sync(self.session.session_handle, client=self.session.client, body=ExecuteStatementRequestBody.from_dict(request_dict))
            operation = FlinkOperation(self.session, response.operation_handle)
            operations.append(operation)
        try:
            yield FlinkCompositeOperation(operations)
        finally:
            for op in reversed(operations):
                op.close().sync()

    @asynccontextmanager
    async def asyncio(self) -> AsyncGenerator[FlinkCompositeOperation, None]:
        operations = []
        for sql in self.sqls:
            request_dict = get_execute_statement_request(sql, self.query_props, self.execute_timeout)
            response = await execute_statement.asyncio(
                self.session.session_handle, client=self.session.client, body=ExecuteStatementRequestBody.from_dict(request_dict)
            )
            operation = FlinkOperation(self.session, response.operation_handle)
            operations.append(operation)
        try:
            yield FlinkCompositeOperation(operations)
        finally:
            for op in reversed(operations):
                await op.close().asyncio()
