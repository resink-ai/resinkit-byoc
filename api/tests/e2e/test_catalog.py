import datetime
from tests.e2e.e2e_base import E2eBase
from resinkit_api.core.logging import get_logger

logger = get_logger(__name__)

class TestCatalog(E2eBase):
    """End-to-end tests for catalog endpoints"""

    def setup_method(self):
        """Setup test by creating a catalog store to use"""
        super().setup_method()
        self.catalog_store_name = "default"
        self.test_paimon_catalog_name = (
            self.get_var("paimon_catalog_name")
            or f"test_paimon_catalog_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

    def teardown_method(self):
        """Clean up by deleting the catalog store"""
        pass

    def test_list_catalogs(self):
        """Test GET /catalogstores/{catalogstore_name}/catalogs endpoint"""
        response = self.get(f"/catalogstores/{self.catalog_store_name}/catalogs")
        self.assert_status_code(response, 200)
        json_data = self.assert_json_response(response)
        assert isinstance(json_data, list)

    def test_list_catalogs_nonexistent_store(self):
        """Test GET /catalogstores/{catalogstore_name}/catalogs with non-existent store"""
        response = self.get("/catalogstores/nonexistent_store/catalogs")
        self.assert_status_code(response, 404)

    def test_get_catalog(self):
        """Test GET /catalogstores/{catalogstore_name}/catalogs/{catalog_name} endpoint"""
        catalog_name = self.get_var("catalog_name") or "my_catalog"
        response = self.get(f"/catalogstores/{self.catalog_store_name}/catalogs/{catalog_name}")
        self.assert_status_code(response, 200)
        json_data = self.assert_json_response(response)
        assert json_data["name"] == catalog_name
        # assert json_data["type"] == "jdbc"
        # Password should not be returned
        assert "password" not in json_data["properties"]

    def test_get_nonexistent_catalog(self):
        """Test GET /catalogstores/{catalogstore_name}/catalogs/{catalog_name} with non-existent catalog"""
        response = self.get(f"/catalogstores/{self.catalog_store_name}/catalogs/nonexistent_catalog")
        self.assert_status_code(response, 404)

    def test_create_paimon_catalog(self):
        """Test POST /catalogstores/{catalogstore_name}/catalogs with Paimon catalog"""
        catalog_data = {
            "name": self.test_paimon_catalog_name,
            "type": "paimon",
            "properties": {
                "warehouse": f"file:/tmp/paimon_test_catalog_{self.test_paimon_catalog_name}",
            },
        }
        response = self.post(f"/catalogstores/{self.catalog_store_name}/catalogs", catalog_data)
        self.assert_status_code(response, 201)
        json_data = self.assert_json_response(response)
        assert json_data["name"] == catalog_data["name"]
        assert json_data["type"] == catalog_data["type"]
    
    def test_delete_paimon_catalog(self):
        """Test DELETE /catalogstores/{catalogstore_name}/catalogs/{catalog_name} with Paimon catalog"""
        response = self.delete(f"/catalogstores/{self.catalog_store_name}/catalogs/{self.test_paimon_catalog_name}")
        logger.info(f"Delete response: {response}")
        self.assert_status_code(response, 204)


    def test_create_hive_catalog(self):
        """Test POST /catalogstores/{catalogstore_name}/catalogs with Hive catalog"""
        catalog_data = {
            "name": "test_hive_catalog",
            "type": "hive",
            "properties": {
                "warehouse": "hdfs://localhost:9000/user/hive/warehouse",
                "metastore-uris": "thrift://localhost:9083",
            },
        }
        response = self.post(f"/catalogstores/{self.catalog_store_name}/catalogs", catalog_data)
        self.assert_status_code(response, 201)
        json_data = self.assert_json_response(response)
        assert json_data["name"] == catalog_data["name"]
        assert json_data["type"] == catalog_data["type"]

    def test_create_catalog_nonexistent_store(self):
        """Test POST /catalogstores/{catalogstore_name}/catalogs with non-existent store"""
        catalog_data = {
            "name": "test_jdbc_catalog",
            "type": "jdbc",
            "properties": {
                "default-database": "test_db",
                "username": "test_user",
                "password": "test_password",
                "base-url": "jdbc:postgresql://localhost:5432",
            },
        }
        response = self.post("/catalogstores/nonexistent_store/catalogs", catalog_data)
        self.assert_status_code(response, 404)

    def test_update_catalog(self):
        """Test PUT /catalogstores/{catalogstore_name}/catalogs/{catalog_name} endpoint"""
        # First create a catalog to update
        catalog_data = {
            "name": "update-test-catalog",
            "type": "jdbc",
            "properties": {
                "default-database": "old_db",
                "username": "old_user",
                "password": "old_password",
                "base-url": "jdbc:postgresql://old-host:5432",
            },
        }
        create_response = self.post(f"/catalogstores/{self.catalog_store_name}/catalogs", catalog_data)
        self.assert_status_code(create_response, 201)

        # Then update the catalog
        updated_data = {
            "name": "update_test_catalog",  # Must match catalog_name in URL
            "type": "jdbc",  # Cannot change type
            "properties": {
                "default-database": "new_db",
                "username": "new_user",
                "password": "new_password",
                "base-url": "jdbc:postgresql://new-host:5432",
            },
        }
        response = self.put(f"/catalogstores/{self.catalog_store_name}/catalogs/{catalog_data['name']}", updated_data)
        self.assert_status_code(response, 200)
        json_data = self.assert_json_response(response)
        assert json_data["name"] == updated_data["name"]
        assert json_data["properties"]["default-database"] == updated_data["properties"]["default-database"]
        assert json_data["properties"]["username"] == updated_data["properties"]["username"]
        # Password should not be returned
        assert "password" not in json_data["properties"]

    def test_update_catalog_name_mismatch(self):
        """Test PUT with catalog name mismatch between URL and body"""
        # First create a catalog to update
        catalog_data = {
            "name": "mismatch_test_catalog",
            "type": "jdbc",
            "properties": {
                "default-database": "test_db",
                "username": "test_user",
                "password": "test_password",
                "base-url": "jdbc:postgresql://localhost:5432",
            },
        }
        create_response = self.post(f"/catalogstores/{self.catalog_store_name}/catalogs", catalog_data)
        self.assert_status_code(create_response, 201)

        # Try to update with mismatched name
        updated_data = {
            "name": "different_name",  # Different from URL
            "type": "jdbc",
            "properties": {
                "default-database": "new_db",
                "username": "new_user",
                "password": "new_password",
                "base-url": "jdbc:postgresql://new-host:5432",
            },
        }
        response = self.put(f"/catalogstores/{self.catalog_store_name}/catalogs/{catalog_data['name']}", updated_data)
        self.assert_status_code(response, 400)

    def test_delete_catalog(self):
        """Test DELETE /catalogstores/{catalogstore_name}/catalogs/{catalog_name} endpoint"""
        # First create a catalog to delete
        catalog_data = {
            "name": "delete_test_catalog",
            "type": "jdbc",
            "properties": {
                "default-database": "test_db",
                "username": "test_user",
                "password": "test_password",
                "base-url": "jdbc:postgresql://localhost:5432",
            },
        }
        create_response = self.post(f"/catalogstores/{self.catalog_store_name}/catalogs", catalog_data)
        self.assert_status_code(create_response, 201)

        # Then delete the catalog
        response = self.delete(f"/catalogstores/{self.catalog_store_name}/catalogs/{catalog_data['name']}")
        self.assert_status_code(response, 204)

        # Verify it's deleted
        get_response = self.get(f"/catalogstores/{self.catalog_store_name}/catalogs/{catalog_data['name']}")
        self.assert_status_code(get_response, 404)

    def test_delete_nonexistent_catalog(self):
        """Test DELETE with non-existent catalog"""
        response = self.delete(f"/catalogstores/{self.catalog_store_name}/catalogs/nonexistent_catalog")
        self.assert_status_code(response, 404)

    def test_catalog_crud_lifecycle(self):
        """Test complete CRUD lifecycle of a catalog"""
        catalog_name = "lifecycle_test_catalog"
        
        # 1. Verify catalog doesn't exist initially
        get_response = self.get(f"/catalogstores/{self.catalog_store_name}/catalogs/{catalog_name}")
        self.assert_status_code(get_response, 404)
        
        # 2. Create the catalog
        catalog_data = {
            "name": catalog_name,
            "type": "jdbc",
            "properties": {
                "default-database": "test_db",
                "username": "test_user",
                "password": "test_password",
                "base-url": "jdbc:postgresql://localhost:5432",
            },
        }
        create_response = self.post(f"/catalogstores/{self.catalog_store_name}/catalogs", catalog_data)
        self.assert_status_code(create_response, 201)
        
        # 3. Verify catalog exists in the list
        list_response = self.get(f"/catalogstores/{self.catalog_store_name}/catalogs")
        self.assert_status_code(list_response, 200)
        catalogs_list = self.assert_json_response(list_response)
        catalog_names = [catalog["name"] for catalog in catalogs_list]
        assert catalog_name in catalog_names
        
        # 4. Get the catalog directly and verify data
        get_response = self.get(f"/catalogstores/{self.catalog_store_name}/catalogs/{catalog_name}")
        self.assert_status_code(get_response, 200)
        json_data = self.assert_json_response(get_response)
        assert json_data["name"] == catalog_data["name"]
        assert json_data["type"] == catalog_data["type"]
        assert json_data["properties"]["default-database"] == catalog_data["properties"]["default-database"]
        assert "password" not in json_data["properties"]
        
        # 5. Update the catalog
        updated_data = {
            "name": catalog_name,
            "type": "jdbc",
            "properties": {
                "default-database": "updated_db",
                "username": "updated_user",
                "password": "updated_password",
                "base-url": "jdbc:postgresql://updated-host:5432",
            },
        }
        update_response = self.put(f"/catalogstores/{self.catalog_store_name}/catalogs/{catalog_name}", updated_data)
        self.assert_status_code(update_response, 200)
        json_data = self.assert_json_response(update_response)
        assert json_data["properties"]["default-database"] == updated_data["properties"]["default-database"]
        
        # 6. Delete the catalog
        delete_response = self.delete(f"/catalogstores/{self.catalog_store_name}/catalogs/{catalog_name}")
        self.assert_status_code(delete_response, 204)
        
        # 7. Verify it's deleted
        get_response = self.get(f"/catalogstores/{self.catalog_store_name}/catalogs/{catalog_name}")
        self.assert_status_code(get_response, 404)
