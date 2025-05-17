from typing import Any, Dict, List

from pydantic import BaseModel, Field, field_validator


class CatalogStoreDefinition(BaseModel):
    """Data model representing a catalog store configuration"""

    name: str = Field(..., description="Unique identifier for the catalog store")
    kind: str = Field(..., description="Type of the catalog store")
    options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Key-value pairs for specific catalog store configurations",
    )

    @field_validator("options")
    @classmethod
    def validate_file_options(cls, v, info):
        """Validate that file catalog stores have the required path option"""
        if info.data.get("kind") == "file":
            if "table.catalog-store.file.path" not in v:
                raise ValueError("File catalog stores must specify 'table.catalog-store.file.path'")
            if not isinstance(v["table.catalog-store.file.path"], str):
                raise ValueError("'table.catalog-store.file.path' must be a string")
        return v


class CatalogStoresResponse(BaseModel):
    """Response model for listing catalog stores"""

    catalogStores: List[CatalogStoreDefinition]
