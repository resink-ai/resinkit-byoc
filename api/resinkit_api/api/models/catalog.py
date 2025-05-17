from typing import Dict, Optional, Any
from pydantic import BaseModel, Field, field_validator


# Define JDBC catalog properties model
class JdbcCatalogProperties(BaseModel):
    default_database: str = Field(..., alias="default-database")
    username: str
    password: str
    base_url: str = Field(..., alias="base-url")

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "default-database": "mydb",
                "username": "user",
                "password": "password",
                "base-url": "jdbc:postgresql://localhost:5432",
            }
        },
    }


# Define Hive catalog properties model
class HiveCatalogProperties(BaseModel):
    hive_conf_dir: Optional[str] = Field(None, alias="hive-conf-dir")
    default_database: Optional[str] = Field("default", alias="default-database")
    hive_version: Optional[str] = Field(None, alias="hive-version")
    hadoop_conf_dir: Optional[str] = Field(None, alias="hadoop-conf-dir")

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "hive-conf-dir": "file:///path/to/hive/conf",
                "default-database": "default",
                "hive-version": "3.1.2",
                "hadoop-conf-dir": "/path/to/hadoop/conf",
            }
        },
    }


# Define catalog request model
class CatalogRequest(BaseModel):
    name: str
    type: str
    properties: Dict[str, Any]

    @field_validator("properties", mode="before")
    def validate_properties(cls, v, info):
        # Access the current values from info.data (Pydantic v2 API)
        if not info.data or "type" not in info.data:
            raise ValueError(f"Type must be specified before properties: {info.data}")

        catalog_type = info.data["type"]
        if catalog_type == "jdbc":
            required_fields = ["default-database", "username", "password", "base-url"]
            for field in required_fields:
                if field not in v:
                    raise ValueError(f"Missing required field for JDBC catalog: {field}")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "my_catalog",
                "type": "jdbc",
                "properties": {
                    "default-database": "mydb",
                    "username": "user",
                    "password": "password",
                    "base-url": "jdbc:postgresql://localhost:5432",
                },
            }
        }
    }


# Define catalog response model (omits sensitive information)
class CatalogResponse(BaseModel):
    name: str
    type: str
    properties: Dict[str, Any]

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "my_catalog",
                "type": "jdbc",
                "properties": {
                    "default-database": "mydb",
                    "username": "user",
                    "base-url": "jdbc:postgresql://localhost:5432",
                },
            }
        }
    }


# Define error response model
class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "error_code": "CATALOG_NOT_FOUND",
                "message": "The specified catalog does not exist",
                "details": "Catalog 'my_catalog' was not found in catalog store 'my_store'",
            }
        }
    }
