import json
import os
import pytest
import requests
from typing import Dict, Any, Optional
from resinkit_api.core.logging import get_logger

logger = get_logger(__name__)


class E2eBase:
    """Base class for E2E tests"""

    def setup_method(self):
        """Setup method that runs before each test method"""
        self.BASE_URL = os.getenv("BASE_URL", "http://localhost:8602")

    def get_var(self, var_name: str, default_value: str = None) -> str:
        """Get a variable from the environment, example: TEST_VAR_catalog_name"""
        env_key = f"TEST_VAR_{var_name}"
        return os.getenv(env_key, default_value)

    def get_url(self, path: str) -> str:
        """Get full URL for a given path"""
        # Add the API version prefix "/api/v1" to all paths
        path_with_prefix = f"/api/v1{path}"
        return f"{self.BASE_URL}{path_with_prefix}"

    def get(self, path: str, headers: Dict[str, str] = None) -> requests.Response:
        """Send a GET request"""
        logger.info(f"GET request to {self.get_url(path)}")
        return requests.get(self.get_url(path), headers=headers)

    def post(self, path: str, data: Dict[str, Any], headers: Dict[str, str] = None) -> requests.Response:
        """Send a POST request with JSON data"""
        logger.info(f"POST request to {self.get_url(path)} with data: {data}")
        return requests.post(self.get_url(path), json=data, headers=headers)

    def put(self, path: str, data: Dict[str, Any], headers: Dict[str, str] = None) -> requests.Response:
        """Send a PUT request with JSON data"""
        logger.info(f"PUT request to {self.get_url(path)} with data: {data}")
        return requests.put(self.get_url(path), json=data, headers=headers)

    def delete(self, path: str, headers: Dict[str, str] = None) -> requests.Response:
        """Send a DELETE request"""
        logger.info(f"DELETE request to {self.get_url(path)}")
        return requests.delete(self.get_url(path), headers=headers)

    def assert_status_code(self, response: requests.Response, expected_code: int) -> None:
        """Assert that the response has the expected status code"""
        assert response.status_code == expected_code, f"Expected status {expected_code}, got {response.status_code}: {response.text}"

    def assert_json_response(
        self,
        response: requests.Response,
        expected_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Assert that the response is JSON and optionally compare with expected data
        Returns the parsed JSON response
        """
        try:
            json_data = response.json()
            logger.info(f"JSON response: {json_data}")
        except json.JSONDecodeError:
            pytest.fail(f"Response is not valid JSON: {response.text}")

        if expected_data:
            assert json_data == expected_data, f"JSON response doesn't match expected data.\nGot: {json_data}\nExpected: {expected_data}"

        return json_data
