from tests.e2e.e2e_base import E2eBase
import requests


class TestTasks(E2eBase):
    """End-to-end tests for Tasks endpoints"""

    def setup_method(self):
        """Setup test environment"""
        super().setup_method()
        # Define test YAML content for task creation
        self.task_yaml = """
task_type: flink_cdc_pipeline
name: MySQL to Doris Sync Pipeline
description: Synchronization of all MySQL tables to Doris
task_timeout_seconds: 300
"""

    def test_create_task_with_yaml(self):
        """Test /tasks/yaml endpoint for creating a task with YAML content"""
        # Make request to create a task with YAML content
        response = requests.post(self.get_url("/tasks/yaml"), headers={"Content-Type": "text/plain", "accept": "application/json"}, data=self.task_yaml)
        self.assert_status_code(response, 202)
        json_data = self.assert_json_response(response)
        assert "status" in json_data, "Response should contain 'status' field"
