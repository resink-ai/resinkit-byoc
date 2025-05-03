import base64
from tests.e2e.e2e_base import E2eBase


class TestPAT(E2eBase):
    """End-to-end tests for Personal Access Token (PAT) endpoints"""

    def setup_method(self):
        """Setup test environment"""
        super().setup_method()
        # Define test PATs for different test cases
        self.valid_pat = self.get_var("valid_pat", "pat_cnk8_")

        
    def test_validate_with_valid_pat_header(self):
        """Test /pat/validate endpoint with a valid PAT in x-resinkit-pat header, this works only for BYOC"""
        # Make request with PAT in x-resinkit-pat header
        response = self.get(
            "/pat/validate",
            headers={"x-resinkit-pat": self.valid_pat}
        )
        self.assert_status_code(response, 200)
        json_data = self.assert_json_response(response)
        assert "permissions" in json_data
        # Check that permissions is either a list or wildcard '*'
        assert isinstance(json_data["permissions"], list) or json_data["permissions"] == '*'
    