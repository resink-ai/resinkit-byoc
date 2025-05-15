
import uuid
from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncGenerator, Dict, Generator, List, Optional

from flink_gateway_api import Client
from flink_gateway_api.api.default import (
    close_session,
    complete_statement,
    execute_statement,
    open_session,
)
from flink_gateway_api.models import (
    CompleteStatementRequestBody,
    CompleteStatementResponseBody,
    ExecuteStatementRequestBody,
    OpenSessionRequestBody,
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
    """
    def __init__(self, client: Client, properties: Dict[str, str] = None, session_name: str = None):
        self.properties = properties or {}
        self.session_handle: Optional[str] = None
        self.session_name = session_name or f"session_{uuid.uuid4()}"
        self.client: Client = client

    async def __aenter__(self):
        response = await open_session.asyncio(
            client=self.client,
            body=OpenSessionRequestBody.from_dict({
                "properties": self.properties,
                "sessionName": self.session_name
            })
        )
        self.session_handle = response.session_handle
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session_handle:
            await close_session.asyncio(self.session_handle, client=self.client)

    def __enter__(self):
        response = open_session.sync(
            client=self.client,
            body=OpenSessionRequestBody.from_dict({
                "properties": self.properties,
                "sessionName": self.session_name
            })
        )
        self.session_handle = response.session_handle
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session_handle:
            close_session.sync(self.session_handle, client=self.client)

    def complete_statement(self) -> 'SessionCompleteStatement':
        return SessionCompleteStatement(self)

    def execute(self, sql: str, query_props: Optional[Dict[str, Any]] = None, execute_timeout: Optional[int] = None) -> 'ExecuteDispatch':
        """Execute a SQL statement in a single session.
        Args:
            sql: SQL statement to execute
            query_props: executionConfig
            execute_timeout: executionTimeout

        Returns: a dispatch, results of which can be fetched synchronously or asynchronously
        """
        return ExecuteDispatch(self, sql, query_props, execute_timeout)

    def execute_all(self, sqls: List[str], query_props: Optional[Dict[str, Any]] = None, execute_timeout: Optional[int] = None) -> 'ExecuteAllDispatch':
        """Execute multiple SQL statements concurrently in a single session.

        Args:
            sqls: List of SQL statements to execute
            query_props: executionConfig
            execute_timeout: executionTimeout

        Returns: a dispatch, results of which can be fetched synchronously or asynchronously
        """
        return ExecuteAllDispatch(self, sqls, query_props, execute_timeout)

class SessionCompleteStatement:
    def __init__(self, session: FlinkSession):
        self.session = session

    def sync(self, position: int, statement: str) -> CompleteStatementResponseBody:
        return complete_statement.sync(
            self.session.session_handle,
            client=self.session.client,
            body=CompleteStatementRequestBody.from_dict({
                "position": position,
                "statement": statement,
            }))

    async def asyncio(self, position: int, statement: str) -> CompleteStatementResponseBody:
        return await complete_statement.asyncio(
            self.session.session_handle,
            client=self.session.client,
            body=CompleteStatementRequestBody.from_dict({
                "position": position,
                "statement": statement,
            }))


class ExecuteDispatch:
    def __init__(self, session: 'FlinkSession', sql: str, query_props=None, execute_timeout=None):
        self.session = session
        self.sql = sql
        self.query_props = query_props
        self.execute_timeout = execute_timeout

    @contextmanager
    def sync(self) -> Generator[FlinkOperation, None, None]:
        request_dict = get_execute_statement_request(self.sql, self.query_props, self.execute_timeout)
        response = execute_statement.sync(
            self.session.session_handle,
            client=self.session.client,
            body=ExecuteStatementRequestBody.from_dict(request_dict)
        )
        operation = FlinkOperation(self.session, response.operation_handle)
        try:
            yield operation
        finally:
            operation.close().sync()

    @asynccontextmanager
    async def asyncio(self) -> AsyncGenerator[FlinkOperation, None]:
        request_dict = get_execute_statement_request(self.sql, self.query_props, self.execute_timeout)
        response = await execute_statement.asyncio(
            self.session.session_handle,
            client=self.session.client,
            body=ExecuteStatementRequestBody.from_dict(request_dict)
        )
        operation = FlinkOperation(self.session, response.operation_handle)
        try:
            yield operation
        finally:
            await operation.close().asyncio()


class ExecuteAllDispatch:
    def __init__(self, session: 'FlinkSession', sqls: List[str], query_props=None, execute_timeout=None):
        self.session = session
        self.sqls = sqls
        self.query_props = query_props
        self.execute_timeout = execute_timeout

    @contextmanager
    def sync(self) -> Generator[FlinkCompositeOperation, None, None]:
        operations = []
        for sql in self.sqls:
            request_dict = get_execute_statement_request(sql, self.query_props, self.execute_timeout)
            response = execute_statement.sync(
                self.session.session_handle,
                client=self.session.client,
                body=ExecuteStatementRequestBody.from_dict(request_dict)
            )
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
                self.session.session_handle,
                client=self.session.client,
                body=ExecuteStatementRequestBody.from_dict(request_dict)
            )
            operation = FlinkOperation(self.session, response.operation_handle)
            operations.append(operation)
        try:
            yield FlinkCompositeOperation(operations)
        finally:
            for op in reversed(operations):
                await op.close().asyncio()
