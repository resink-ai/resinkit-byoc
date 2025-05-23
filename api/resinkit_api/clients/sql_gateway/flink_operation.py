from dataclasses import dataclass
from typing import TYPE_CHECKING, List

import pandas as pd
from flink_gateway_api import Client
from flink_gateway_api.api.default import (
    cancel_operation,
    close_operation,
    get_operation_status,
)
from flink_gateway_api.models import (
    OperationStatusResponseBody,
)
from resinkit_api.clients.sql_gateway.session_utils import (
    FetchResultData,
    create_dataframe,
    fetch_results_async_gen,
    fetch_results_gen,
)
from resinkit_api.core.logging import get_logger

if TYPE_CHECKING:
    from .flink_session import FlinkSession


logger = get_logger(__name__)


@dataclass
class ResultsFetchOpts:
    poll_interval_secs: float = 0.1
    max_poll_secs: float = 10  # set to 0 or negative pull once
    n_row_limit: int = 500

    def __post_init__(self):
        if self.poll_interval_secs < 0:
            raise ValueError(f"poll_interval_secs must be non-negative, got {self.poll_interval_secs}")

        if self.n_row_limit < 0:
            raise ValueError(f"n_row_limit must be non-negative, got {self.n_row_limit}")


PULL_ONCE_OPTS = ResultsFetchOpts(max_poll_secs=0)


class FlinkOperation:
    def __init__(self, session: "FlinkSession", operation_handle: str):
        self.session = session
        self.operation_handle = operation_handle
        self.client: "Client" = session.client

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close().asyncio()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close().sync()

    def status(self) -> "OperationStatus":
        return OperationStatus(self)

    def fetch(self, polling_opts: ResultsFetchOpts = ResultsFetchOpts()) -> "OperationFetch":
        return OperationFetch(self, polling_opts)

    def fetch_once(self) -> "OperationFetch":
        return OperationFetch(self, PULL_ONCE_OPTS)

    def close(self) -> "OperationClose":
        return OperationClose(self)

    def cancel(self) -> "OperationCancel":
        return OperationCancel(self)


class OperationStatus:
    def __init__(self, operation: "FlinkOperation"):
        self.operation = operation

    def sync(self) -> OperationStatusResponseBody:
        return get_operation_status.sync(self.operation.session.session_handle, self.operation.operation_handle, client=self.operation.client)

    async def asyncio(self) -> OperationStatusResponseBody:
        return await get_operation_status.asyncio(self.operation.session.session_handle, self.operation.operation_handle, client=self.operation.client)


class OperationFetch:
    def __init__(self, operation: "FlinkOperation", fetch_opts: ResultsFetchOpts):
        self.operation = operation
        self._fetch_opts = fetch_opts
        self._token = "0"  # Initial token, might need to be configurable

    def sync(self) -> tuple[pd.DataFrame, FetchResultData]:
        all_rows = []
        columns = None
        job_id = None
        for res_data in fetch_results_gen(
            self.operation.client,
            self.operation.session.session_handle,
            self.operation.operation_handle,
            poll_interval_secs=self._fetch_opts.poll_interval_secs,
            max_poll_secs=self._fetch_opts.max_poll_secs,
            n_row_limit=self._fetch_opts.n_row_limit,
        ):
            if columns is None and res_data.columns is not None:
                columns = res_data.columns
            if job_id is None and hasattr(res_data, "job_id"):
                job_id = res_data.job_id
            all_rows.extend(res_data.data)
        return create_dataframe(all_rows[: self._fetch_opts.n_row_limit], columns), res_data

    async def asyncio(self) -> tuple[pd.DataFrame, FetchResultData]:
        columns, all_rows = None, []
        job_id = None
        async for res_data in fetch_results_async_gen(
            self.operation.client,
            self.operation.session.session_handle,
            self.operation.operation_handle,
            poll_interval_secs=self._fetch_opts.poll_interval_secs,
            max_poll_secs=self._fetch_opts.max_poll_secs,
            n_row_limit=self._fetch_opts.n_row_limit,
        ):
            res_data: FetchResultData
            if columns is None and res_data.columns is not None:
                columns = res_data.columns
            if job_id is None and hasattr(res_data, "job_id"):
                job_id = res_data.job_id
            all_rows.extend(res_data.data)
        return create_dataframe(all_rows[: self._fetch_opts.n_row_limit], columns), res_data


class OperationClose:
    def __init__(self, operation: FlinkOperation):
        self.operation = operation

    def sync(self) -> OperationStatusResponseBody:
        return close_operation.sync(self.operation.session.session_handle, self.operation.operation_handle, client=self.operation.client)

    async def asyncio(self) -> OperationStatusResponseBody:
        return await close_operation.asyncio(self.operation.session.session_handle, self.operation.operation_handle, client=self.operation.client)


class OperationCancel:
    def __init__(self, operation: FlinkOperation):
        self.operation = operation

    def sync(self) -> OperationStatusResponseBody:
        return cancel_operation.sync(self.operation.session.session_handle, self.operation.operation_handle, client=self.operation.client)

    async def asyncio(self) -> OperationStatusResponseBody:
        return await cancel_operation.asyncio(self.operation.session.session_handle, self.operation.operation_handle, client=self.operation.client)


class FlinkCompositeOperation:
    def __init__(self, operations: List["FlinkOperation"]):
        self.operations = operations

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for op in reversed(self.operations):
            op.close().sync()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        for op in reversed(self.operations):
            await op.close().asyncio()

    def fetch_all(self, fetch_opts: "ResultsFetchOpts" = ResultsFetchOpts()) -> List[tuple[pd.DataFrame, str]]:
        results = []
        for op in self.operations:
            results.append(op.fetch(fetch_opts).sync())
        return results

    async def fetch_all_async(self, fetch_opts: "ResultsFetchOpts" = ResultsFetchOpts()) -> List[tuple[pd.DataFrame, str]]:
        results = []
        for op in self.operations:
            results.append(await op.fetch(fetch_opts).asyncio())
        return results
