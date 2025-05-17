import os
import tempfile
import httpx
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

from resinkit_api.core.config import settings
from resinkit_api.core.logging import get_logger

logger = get_logger(__name__)


class FlinkResourceManager:
    """
    Manages Flink resources like JAR files by finding them in standard locations
    or downloading them when necessary.
    """

    def __init__(self):
        """Initialize the Flink Resource Manager."""
        self.flink_home = settings.FLINK_HOME
        self.flink_cdc_home = settings.FLINK_CDC_HOME
        self.temp_dir = tempfile.mkdtemp(prefix="flink_resources_")
        self.downloaded_resources: Dict[str, str] = {}  # Maps URLs to local paths

    async def process_resources(self, resources_config: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Process resources configuration and return paths to all required resources.

        Args:
            resources_config: Dictionary containing resources configuration

        Returns:
            Dictionary with resource types as keys and lists of file paths as values
        """
        result = {"jar_paths": [], "classpath_jars": []}

        # Process Flink CDC jars
        if "flink_cdc_jars" in resources_config:
            for jar in resources_config["flink_cdc_jars"]:
                path = await self._resolve_jar(jar)
                if path:
                    if jar.get("type") == "classpath":
                        result["classpath_jars"].append(path)
                    else:
                        result["jar_paths"].append(path)

        # Process regular Flink jars
        if "flink_jars" in resources_config:
            for jar in resources_config["flink_jars"]:
                path = await self._resolve_jar(jar)
                if path:
                    if jar.get("type") == "classpath":
                        result["classpath_jars"].append(path)
                    else:
                        result["jar_paths"].append(path)

        return result

    async def _resolve_jar(self, jar_config: Dict[str, Any]) -> Optional[str]:
        """
        Resolve the path to a JAR file by finding it in standard locations
        or downloading it if necessary.

        Args:
            jar_config: Configuration for the JAR file

        Returns:
            Path to the JAR file or None if it cannot be resolved
        """
        # Check if we already have a location specified
        jar_location = jar_config.get("location") or jar_config.get("download_link")
        if not jar_location:
            logger.warning(f"No location specified for JAR {jar_config.get('name', 'unknown')}")
            return None

        # If we've already downloaded this resource, return the cached path
        if jar_location in self.downloaded_resources:
            return self.downloaded_resources[jar_location]

        # Extract the filename from the URL
        jar_filename = os.path.basename(urlparse(jar_location).path)

        # Check standard locations first
        standard_paths = self._find_in_standard_locations(jar_filename)
        if standard_paths:
            logger.info(f"Found JAR {jar_filename} in standard location: {standard_paths}")
            return standard_paths

        # If not found and download is allowed, download the JAR
        if jar_config.get("source") == "download":
            try:
                download_path = await self._download_jar(jar_location)
                if download_path:
                    logger.info(f"Downloaded JAR {jar_filename} to {download_path}")
                    self.downloaded_resources[jar_location] = download_path
                    return download_path
            except Exception as e:
                logger.error(f"Failed to download JAR {jar_filename}: {str(e)}")

        logger.warning(f"Could not resolve JAR {jar_filename}")
        return None

    def _find_in_standard_locations(self, jar_filename: str) -> Optional[str]:
        """
        Look for a JAR file in standard locations.

        Args:
            jar_filename: Name of the JAR file

        Returns:
            Path to the JAR file or None if not found
        """
        # Check in FLINK_HOME/lib
        flink_lib_path = os.path.join(self.flink_home, "lib", jar_filename)
        if os.path.exists(flink_lib_path):
            return flink_lib_path

        # Check in FLINK_CDC_HOME/lib if it exists
        if self.flink_cdc_home:
            flink_cdc_lib_path = os.path.join(self.flink_cdc_home, "lib", jar_filename)
            if os.path.exists(flink_cdc_lib_path):
                return flink_cdc_lib_path

        # Check in FLINK_HOME/plugins
        plugins_dir = os.path.join(self.flink_home, "plugins")
        if os.path.exists(plugins_dir):
            for root, _, files in os.walk(plugins_dir):
                if jar_filename in files:
                    return os.path.join(root, jar_filename)

        return None

    async def _download_jar(self, url: str) -> Optional[str]:
        """
        Download a JAR file from a URL.

        Args:
            url: URL to download the JAR from

        Returns:
            Path to the downloaded JAR file or None if download failed
        """
        jar_filename = os.path.basename(urlparse(url).path)
        target_path = os.path.join(self.temp_dir, jar_filename)

        # Skip download if file already exists
        if os.path.exists(target_path):
            return target_path

        # Create temp directory if it doesn't exist
        Path(self.temp_dir).mkdir(parents=True, exist_ok=True)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                if response.status_code != 200:
                    logger.error(f"Failed to download JAR {url}: HTTP {response.status_code}")
                    return None

                with open(target_path, "wb") as f:
                    f.write(response.content)

            logger.info(f"Successfully downloaded {url} to {target_path}")
            return target_path
        except Exception as e:
            logger.error(f"Error downloading {url}: {str(e)}")
            # Remove partially downloaded file if it exists
            if os.path.exists(target_path):
                os.remove(target_path)
            return None

    def cleanup(self):
        """
        Clean up temporary resources downloaded by the manager.
        """
        if os.path.exists(self.temp_dir):
            import shutil

            try:
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
            except Exception as e:
                logger.error(f"Failed to clean up temporary directory {self.temp_dir}: {str(e)}")
