import asyncio
from dataclasses import dataclass
import time
from typing import Any, Dict, List, Optional, AsyncGenerator, Generator

import pandas as pd
from flink_gateway_api import Client, errors
from flink_gateway_api.api.default import fetch_results
from flink_gateway_api.models import FetchResultsResponseBody, ResultType, RowKind, RowFormat
from flink_gateway_api.types import UNSET

from resinkit_api.core.logging import get_logger

logger = get_logger(__name__)


def map_flink_to_pandas_dtype(flink_type: str) -> str:
    """
    Map Flink SQL types to pandas dtypes
    """
    # see https://pandas.pydata.org/docs/user_guide/basics.html#basics-dtypes
    type_mapping = {
        "INTEGER": "Int64",
        "BIGINT": "Int64",
        "SMALLINT": "Int16",
        "TINYINT": "Int8",
        "FLOAT": "Float32",
        "DOUBLE": "Float64",
        "DECIMAL": "Float64",
        "BOOLEAN": "boolean",
        "CHAR": "string",
        "VARCHAR": "string",
        "STRING": "string",
        "DATE": "datetime64[ns]",
        "TIME": "datetime64[ns]",
        "TIMESTAMP": "datetime64[ns]",
    }
    return type_mapping.get(flink_type, "object")


def create_dataframe(data: List[List[Any]], columns: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Create a pandas DataFrame with proper data types based on Flink column definitions

    Args:
        data: List of data rows
        columns: List of column definitions from Flink

    Returns:
        pandas.DataFrame: DataFrame with proper data types
    """
    if not columns and not data:
        return pd.DataFrame()
    if not columns and data:
        return pd.DataFrame(data)
    if not data:
        # Create empty DataFrame with proper columns if no data
        df = pd.DataFrame(columns=[col["name"] for col in columns])
    else:
        # Create DataFrame from data
        df = pd.DataFrame(data, columns=[col["name"] for col in columns])

    # Set proper data types
    for column in columns:
        col_name = column["name"]
        flink_type = column["logicalType"]["type"]
        pandas_dtype = map_flink_to_pandas_dtype(flink_type)

        try:
            df[col_name] = df[col_name].astype(pandas_dtype)
        except Exception as e:
            print(f"Warning: Could not convert column {col_name} to {pandas_dtype}: {str(e)}")

    return df


def pd_get_cell_value(df: pd.DataFrame, row_idx: int, col_name: str, default: Any = None) -> Any:
    """
    Get the value of a cell in a row based on the column name.
    If the row index is out of bounds or the column name is not found, return the default value.
    """
    if row_idx < 0 or row_idx >= len(df):
        if default is not None:
            return default
        raise ValueError(f"Row index {row_idx} is out of bounds for DataFrame with {len(df)} rows")
    if col_name not in df.columns:
        if default is not None:
            return default
        raise ValueError(f"Column name {col_name} not found in DataFrame")
    return df.iloc[row_idx][col_name]


@dataclass
class FetchResultData:
    columns: List[Dict[str, Any]]
    data: List[List[Any]]
    eos: bool
    next_url: str | None = None
    job_id: str | None = None
    is_query_result: bool | None = None

    @staticmethod
    def result_ok():
        return FetchResultData(
            columns=[
                {
                    "name": "result",
                    "logicalType": {
                        "type": "VARCHAR",
                        "nullable": True,
                        "length": 2147483647,
                    },
                    "comment": None,
                }
            ],
            data=[["OK"]],
            eos=True,
            next_url=None,
            job_id=None,
        )


def get_fetch_result_data(response: FetchResultsResponseBody | None) -> FetchResultData:
    """
    Extract columns and data from the result
    Args:
        response: FetchResultsResponseBody object.
        Example:
        {'nextResultUri': '/v2/sessions/75066e3a-9720-4f33-8763-f840c20a44ae/operations/236d8658-714c-4ad7-802b-ade363060a05/result/0?rowFormat=JSON', 'resultType': 'NOT_READY'}
        {
            'isQueryResult': False,
            'nextResultUri': '/v2/sessions/75066e3a-9720-4f33-8763-f840c20a44ae/operations/236d8658-714c-4ad7-802b-ade363060a05/result/1?rowFormat=JSON',
            'resultKind': 'SUCCESS',
            'resultType': 'PAYLOAD',
            'results': {
                'columns': [{'name': 'result', 'logicalType': {'type': 'VARCHAR', 'nullable': True, 'length': 2147483647}, 'comment': None}],
                'columnInfos': [],
                'data': [{'kind': 'INSERT', 'fields': ['OK']}],
                'fieldGetters': [],
                'rowFormat': 'JSON',
            },
        }
        {
            'isQueryResult': True,
            'jobID': '08c4b4cf65b01c41470cd1d8445de410',
            'resultKind': 'SUCCESS_WITH_CONTENT',
            'resultType': 'EOS',
            'results': {
                'columns': [
                    {'name': 'user_id', 'logicalType': {'type': 'BIGINT', 'nullable': False}, 'comment': None},
                    {'name': 'item_id', 'logicalType': {'type': 'BIGINT', 'nullable': True}, 'comment': None},
                    {'name': 'behavior', 'logicalType': {'type': 'VARCHAR', 'nullable': True, 'length': 2147483647}, 'comment': None},
                    {'name': 'dt', 'logicalType': {'type': 'VARCHAR', 'nullable': False, 'length': 2147483647}, 'comment': None},
                ],
                'columnInfos': [],
                'data': [],
                'fieldGetters': [],
                'rowFormat': 'JSON',
            },
        }
    Returns: FetchResultData object
    """
    if not response:
        return FetchResultData(columns=[], data=[], eos=True, next_url=None)
    eos = response.result_type == ResultType.EOS
    next_url = None
    job_id = None
    is_query_result = None
    if response.additional_properties:
        is_query_result = response.additional_properties.get("isQueryResult")
    if response.next_result_uri is not UNSET:
        next_url = response.next_result_uri
    if response.job_id is not UNSET:
        job_id = response.job_id

    if response.results is UNSET:
        return FetchResultData(columns=[], data=[], eos=eos, next_url=next_url, job_id=job_id)
    res_results = response.results.to_dict()
    cols = res_results.get("columns") or res_results.get("columnInfos", [])
    data = []
    for row in res_results.get("data", []):
        if row["kind"] == RowKind.INSERT:
            data.append(row.get("fields", []))
    return FetchResultData(columns=cols, data=data, eos=eos, next_url=next_url, job_id=job_id, is_query_result=is_query_result)


def get_execute_statement_request(
    sql: str,
    query_props: Optional[Dict[str, Any]] = None,
    execute_timeout: Optional[int] = None,
):
    request_dict = {
        "statement": sql,
    }

    if query_props:
        request_dict["properties"] = query_props

    if execute_timeout:
        request_dict["execution_timeout"] = execute_timeout
    return request_dict


async def fetch_results_async_gen(
    client: Client,
    session_handle: str,
    operation_handle: str,
    row_format: RowFormat = RowFormat.JSON,
    poll_interval_secs: float = 0.1,
    max_poll_secs: Optional[float] = None,
    n_row_limit: Optional[int] = None,
) -> AsyncGenerator[FetchResultData, None]:
    """
    Fetch all results from Flink SQL Gateway until EOS is reached using async client

    Args:
        client: Async client instance
        session_handle: Session handle string
        operation_handle: Operation handle string
        row_format: Format for the returned rows (JSON or CSV)
        poll_interval_secs: Time to wait between polling
        max_poll_secs: Maximum time to poll
        n_row_limit: Maximum number of rows to fetch

    YieldType:
        tuple: (list of all data rows, list of column definitions)
    SendType: None
    ReturnType: None
    """
    next_url = None
    n_rows = 0
    tic = asyncio.get_event_loop().time()
    while True:
        result: FetchResultsResponseBody | None = None
        if next_url is not None:
            raw_response = await client.get_async_httpx_client().request(
                method="GET",
                url=str(next_url),
                params={"rowFormat": row_format},
            )
            if raw_response.status_code == 200:
                result = FetchResultsResponseBody.from_dict(raw_response.json())
            elif client.raise_on_unexpected_status:
                raise errors.UnexpectedStatus(raw_response.status_code, raw_response.content)
        else:
            result = await fetch_results.asyncio(session_handle, operation_handle, 0, client=client, row_format=row_format)
        logger.debug(f"Fetch result: {result.to_dict() if result else None}")
        res_data = get_fetch_result_data(result)
        if res_data.data:
            n_rows += len(res_data.data)
            yield res_data
        if res_data.eos or res_data.next_url is None:
            break
        if n_row_limit is not None and n_rows >= n_row_limit:
            break
        if max_poll_secs is not None and (asyncio.get_event_loop().time() - tic) >= max_poll_secs:
            break
        # break if the result is not a query result
        next_url = res_data.next_url
        await asyncio.sleep(poll_interval_secs)


def fetch_results_gen(
    client: Client,
    session_handle: str,
    operation_handle: str,
    row_format: RowFormat = RowFormat.JSON,
    poll_interval_secs: float = 0.1,
    max_poll_secs: Optional[float] = None,
    n_row_limit: Optional[int] = None,
) -> Generator[FetchResultData, None, None]:
    """
    Fetch all results from Flink SQL Gateway until EOS is reached using sync client

    Args:
        client: Sync client instance
        session_handle: Session handle string
        operation_handle: Operation handle string
        row_format: Format for the returned rows (JSON or CSV)
        poll_interval_secs: Time to wait between polling
        max_poll_secs: Maximum time to poll
        n_row_limit: Maximum number of rows to fetch

    YieldType:
        tuple: (list of all data rows, list of column definitions)
    SendType: None
    ReturnType: None
    """
    next_url = None
    n_rows = 0
    tic = time.time()

    while True:
        result: FetchResultsResponseBody | None = None
        if next_url is not None:
            raw_response = client.get_httpx_client().request(
                method="GET",
                url=str(next_url),
                params={"rowFormat": row_format},
            )
            if raw_response.status_code == 200:
                result = FetchResultsResponseBody.from_dict(raw_response.json())
            elif client.raise_on_unexpected_status:
                raise errors.UnexpectedStatus(raw_response.status_code, raw_response.content)
        else:
            result = fetch_results.sync(session_handle, operation_handle, 0, client=client, row_format=row_format)

        logger.debug(f"Fetch result: {result.to_dict() if result else None}")
        res_data = get_fetch_result_data(result)

        if res_data.data:
            n_rows += len(res_data.data)
            yield res_data

        if res_data.eos or res_data.next_url is None:
            break

        if n_row_limit is not None and n_rows >= n_row_limit:
            break

        if max_poll_secs is not None and (time.time() - tic) >= max_poll_secs:
            break

        next_url = res_data.next_url
        time.sleep(poll_interval_secs)
