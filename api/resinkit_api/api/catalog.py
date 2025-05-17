from typing import List
from fastapi import APIRouter, Path, Body, HTTPException, status

from resinkit_api.api.models.catalog import (
    CatalogResponse,
    ErrorResponse,
    CatalogRequest,
)
from resinkit_api.core.logging import get_logger
from resinkit_api.services import get_service_manager

logger = get_logger(__name__)
router = APIRouter()


# API Endpoints
@router.get(
    "/catalogstores/{catalogstore_name}/catalogs",
    response_model=List[CatalogResponse],
    status_code=status.HTTP_200_OK,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def list_catalogs(
    catalogstore_name: str = Path(..., description="The name of the catalog store"),
):
    """
    Retrieves a list of all catalogs configured within the specified catalog store.
    """
    try:
        return await get_service_manager().catalog.list(catalogstore_name)
    except HTTPException:
        raise
    except Exception as e:
        # Log the error and return a more informative error message
        logger.error(f"Error listing catalogs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An error occurred while listing catalogs",
                "details": str(e),
            },
        )


@router.get(
    "/catalogstores/{catalogstore_name}/catalogs/{catalog_name}",
    response_model=CatalogResponse,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def get_catalog(
    catalogstore_name: str = Path(..., description="The name of the catalog store"),
    catalog_name: str = Path(..., description="The name of the catalog to retrieve"),
):
    """
    Retrieves the configuration details of a specific catalog.
    """
    try:
        return await get_service_manager().catalog.get(catalogstore_name, catalog_name)
    except HTTPException:
        raise
    except Exception as e:
        # Log the error and return a more informative error message
        logger.error(f"Error getting catalog: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An error occurred while retrieving the catalog",
                "details": str(e),
            },
        )


@router.post(
    "/catalogstores/{catalogstore_name}/catalogs",
    response_model=CatalogResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def create_catalog(
    catalog: CatalogRequest = Body(...),
    catalogstore_name: str = Path(..., description="The name of the catalog store"),
):
    """
    Creates a new catalog (either JDBC or Hive) within the specified catalog store.
    """
    try:
        return await get_service_manager().catalog.create(catalogstore_name, catalog)
    except HTTPException:
        raise
    except ValueError as ve:
        # Handle validation errors
        logger.error(f"Validation error creating catalog: {str(ve)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": f"Validation error: {str(ve)}",
                "details": None,
            },
        )
    except Exception as e:
        # Log the error and return a more informative error message
        logger.error(f"Error creating catalog: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An error occurred while creating the catalog",
                "details": str(e),
            },
        )


@router.put(
    "/catalogstores/{catalogstore_name}/catalogs/{catalog_name}",
    response_model=CatalogResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def update_catalog(
    catalog: CatalogRequest = Body(...),
    catalogstore_name: str = Path(..., description="The name of the catalog store"),
    catalog_name: str = Path(..., description="The name of the catalog to update"),
):
    """
    Updates the configuration of an existing catalog. This is typically a full replacement
    of the configuration for the given catalog name. The type of the catalog cannot be changed via PUT.
    """
    try:
        return await get_service_manager().catalog.update(catalogstore_name, catalog_name, catalog)
    except HTTPException:
        raise
    except Exception as e:
        # Log the error and return a more informative error message
        logger.error(f"Error updating catalog: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An error occurred while updating the catalog",
                "details": str(e),
            },
        )


@router.delete(
    "/catalogstores/{catalogstore_name}/catalogs/{catalog_name}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def delete_catalog(
    catalogstore_name: str = Path(..., description="The name of the catalog store"),
    catalog_name: str = Path(..., description="The name of the catalog to delete"),
):
    """
    Deletes a specific catalog from the catalog store.
    """
    try:
        await get_service_manager().catalog.delete(catalogstore_name, catalog_name)
        # No content is returned for successful deletion
        return None
    except HTTPException:
        raise
    except Exception as e:
        # Log the error and return a more informative error message
        logger.error(f"Error deleting catalog: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An error occurred while deleting the catalog",
                "details": str(e),
            },
        )
