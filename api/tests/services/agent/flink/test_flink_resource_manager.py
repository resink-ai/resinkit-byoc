import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock, AsyncMock

from resinkit_api.services.agent.flink.flink_resource_manager import FlinkResourceManager


@pytest.fixture
def resource_manager():
    with patch('resinkit_api.services.agent.flink.flink_resource_manager.settings') as mock_settings:
        # Mock the settings required by the resource manager
        mock_settings.FLINK_HOME = "/mock/flink/home"
        mock_settings.FLINK_CDC_HOME = "/mock/flink/cdc/home"
        
        # Create the resource manager
        manager = FlinkResourceManager()
        
        # Mock the temp directory to avoid actual file system operations
        manager.temp_dir = tempfile.mkdtemp(prefix="test_flink_resources_")
        
        yield manager
        
        # Clean up the temp directory after the test
        import shutil
        if os.path.exists(manager.temp_dir):
            shutil.rmtree(manager.temp_dir)


@pytest.mark.asyncio
async def test_process_resources_with_existing_jars(resource_manager):
    """Test processing resources when JAR files already exist in standard locations."""
    # Mock the _find_in_standard_locations method to return a fixed path
    resource_manager._find_in_standard_locations = MagicMock(
        return_value="/mock/flink/home/lib/mysql-connector-java-8.0.27.jar"
    )
    
    # Sample resource config
    resource_config = {
        "flink_cdc_jars": [
            {
                "name": "MySQL Pipeline Connector 3.3.0",
                "type": "lib", 
                "source": "download",
                "location": "https://repo1.maven.org/maven2/org/apache/flink/flink-cdc-pipeline-connector-mysql/3.3.0/flink-cdc-pipeline-connector-mysql-3.3.0.jar"
            }
        ],
        "flink_jars": [
            {
                "name": "MySQL Connector Java",
                "type": "classpath",
                "source": "download",
                "location": "https://repo1.maven.org/maven2/mysql/mysql-connector-java/8.0.27/mysql-connector-java-8.0.27.jar"
            }
        ]
    }
    
    # Process the resources
    result = await resource_manager.process_resources(resource_config)
    
    # Verify that the standard locations were checked
    resource_manager._find_in_standard_locations.assert_called()
    
    # Verify the result contains the correct paths
    assert len(result["jar_paths"]) == 1
    assert len(result["classpath_jars"]) == 1
    assert result["jar_paths"][0] == "/mock/flink/home/lib/mysql-connector-java-8.0.27.jar"
    assert result["classpath_jars"][0] == "/mock/flink/home/lib/mysql-connector-java-8.0.27.jar"


@pytest.mark.asyncio
async def test_process_resources_with_downloads(resource_manager):
    """Test processing resources when JAR files need to be downloaded."""
    # Mock the _find_in_standard_locations method to return None (not found)
    resource_manager._find_in_standard_locations = MagicMock(return_value=None)
    
    # Mock the _download_jar method to return a fixed path
    mock_download_path = os.path.join(resource_manager.temp_dir, "downloaded-mysql-connector.jar")
    resource_manager._download_jar = AsyncMock(return_value=mock_download_path)
    
    # Sample resource config
    resource_config = {
        "flink_cdc_jars": [
            {
                "name": "MySQL Connector Java",
                "type": "lib",
                "source": "download",
                "location": "https://repo1.maven.org/maven2/mysql/mysql-connector-java/8.0.27/mysql-connector-java-8.0.27.jar"
            }
        ]
    }
    
    # Process the resources
    result = await resource_manager.process_resources(resource_config)
    
    # Verify the _download_jar method was called
    resource_manager._download_jar.assert_called_once()
    
    # Verify the result contains the correct path
    assert len(result["jar_paths"]) == 1
    assert result["jar_paths"][0] == mock_download_path


@pytest.mark.asyncio
async def test_resolve_jar_with_cached_resource(resource_manager):
    """Test that the resource manager correctly caches downloaded resources."""
    # Add a resource to the cache
    resource_url = "https://repo1.maven.org/maven2/mysql/mysql-connector-java/8.0.27/mysql-connector-java-8.0.27.jar"
    cached_path = "/mock/cached/path/mysql-connector-java-8.0.27.jar"
    resource_manager.downloaded_resources[resource_url] = cached_path
    
    # Mock the _find_in_standard_locations method to make sure it's not called
    resource_manager._find_in_standard_locations = MagicMock()
    
    # Mock the _download_jar method to make sure it's not called
    resource_manager._download_jar = AsyncMock()
    
    # Resolve the jar
    jar_config = {
        "name": "MySQL Connector Java",
        "type": "lib",
        "source": "download",
        "location": resource_url
    }
    
    result = await resource_manager._resolve_jar(jar_config)
    
    # Verify the cached path was returned
    assert result == cached_path
    
    # Verify that _find_in_standard_locations and _download_jar were not called
    resource_manager._find_in_standard_locations.assert_not_called()
    resource_manager._download_jar.assert_not_called()


def test_find_in_standard_locations(resource_manager):
    """Test finding JARs in standard locations."""
    # Mock os.path.exists to simulate files in standard locations
    with patch('os.path.exists') as mock_exists, patch('os.walk') as mock_walk:
        # Configure mock_exists to return True only for specific paths
        def exists_side_effect(path):
            if path == "/mock/flink/home/lib/mysql-connector-java-8.0.27.jar":
                return True
            if path == "/mock/flink/cdc/home/lib/flink-cdc-connector-mysql-3.3.0.jar":
                return True
            if path == "/mock/flink/home/plugins":
                return True
            return False
        
        mock_exists.side_effect = exists_side_effect
        
        # Mock os.walk to return some plugin files
        mock_walk.return_value = [
            ("/mock/flink/home/plugins/mysql", [], ["mysql-plugin.jar"])
        ]
        
        # Test file in FLINK_HOME/lib
        result1 = resource_manager._find_in_standard_locations("mysql-connector-java-8.0.27.jar")
        assert result1 == "/mock/flink/home/lib/mysql-connector-java-8.0.27.jar"
        
        # Test file in FLINK_CDC_HOME/lib
        result2 = resource_manager._find_in_standard_locations("flink-cdc-connector-mysql-3.3.0.jar")
        assert result2 == "/mock/flink/cdc/home/lib/flink-cdc-connector-mysql-3.3.0.jar"
        
        # Test file in plugins directory
        result3 = resource_manager._find_in_standard_locations("mysql-plugin.jar")
        assert result3 == "/mock/flink/home/plugins/mysql/mysql-plugin.jar"
        
        # Test file that doesn't exist
        result4 = resource_manager._find_in_standard_locations("nonexistent.jar")
        assert result4 is None


@pytest.mark.asyncio
async def test_download_jar(resource_manager):
    """Test downloading a JAR file."""
    url = "https://example.com/flink-test.jar"
    target_path = os.path.join(resource_manager.temp_dir, "flink-test.jar")
    
    # Mock aiohttp.ClientSession to avoid actual HTTP requests
    mock_response = MagicMock()
    mock_response.status = 200
    
    mock_content = MagicMock()
    mock_content.read = AsyncMock(side_effect=[b"test data", b""])
    mock_response.content = mock_content
    
    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = AsyncMock(return_value=mock_response)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        result = await resource_manager._download_jar(url)
        
        # Verify the result is the target path
        assert result == target_path
        
        # Verify the file was created
        assert os.path.exists(target_path)
        
        # Verify the content was written correctly
        with open(target_path, 'rb') as f:
            content = f.read()
            assert content == b"test data"


def test_cleanup(resource_manager):
    """Test cleanup of temporary resources."""
    # Create a test file in the temporary directory
    test_file = os.path.join(resource_manager.temp_dir, "test.jar")
    with open(test_file, 'w') as f:
        f.write("test")
    
    # Verify the file exists
    assert os.path.exists(test_file)
    
    # Mock shutil.rmtree to avoid actual file system operations
    with patch('shutil.rmtree') as mock_rmtree:
        resource_manager.cleanup()
        
        # Verify that rmtree was called with the temp directory
        mock_rmtree.assert_called_once_with(resource_manager.temp_dir) 