from fastapi import APIRouter, HTTPException, Path, Body, Response, status

from resinkit_api.api.models.catalogstore import (
    CatalogStoreDefinition,
    CatalogStoresResponse,
)
from resinkit_api.services import get_service_manager
from resinkit_api.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "/catalogstores",
    response_model=CatalogStoresResponse,
    status_code=status.HTTP_200_OK,
)
async def list_catalog_stores():
    """
    Retrieves a list of all configured catalog stores.

    Returns:
        A JSON object containing a list of catalog store definitions.

    Raises:
        HTTPException: 500 Internal Server Error if there's an issue retrieving the list.
    """
    logger.info("Retrieving all catalog stores")
    try:
        catalog_stores = await get_service_manager().catalogstore.list()
        logger.debug(f"Found {len(catalog_stores)} catalog stores")
        return CatalogStoresResponse(catalogStores=catalog_stores)
    except Exception as e:
        logger.error(f"Failed to retrieve catalog stores: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve catalog stores: {str(e)}",
        )


@router.get(
    "/catalogstores/{catalogstore_name}",
    response_model=CatalogStoreDefinition,
    status_code=status.HTTP_200_OK,
)
async def get_catalog_store(
    catalogstore_name: str = Path(..., description="The unique name of the catalog store to retrieve"),
):
    """
    Retrieves the definition of a specific catalog store identified by its name.

    Args:
        catalogstore_name: The unique name of the catalog store to retrieve.

    Returns:
        The Catalog Store Definition object for the requested store.

    Raises:
        HTTPException: 404 Not Found if no catalog store with the specified name exists.
        HTTPException: 500 Internal Server Error if there's an issue retrieving the store details.
    """
    logger.info(f"Retrieving catalog store: {catalogstore_name}")
    try:
        store = await get_service_manager().catalogstore.get(catalogstore_name)
        logger.debug(f"Successfully retrieved catalog store: {catalogstore_name}")
        return store
    except HTTPException as he:
        logger.error(f"HTTP error retrieving catalog store {catalogstore_name}: {str(he)}")
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve catalog store {catalogstore_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve catalog store: {str(e)}",
        )


@router.post(
    "/catalogstores",
    response_model=CatalogStoreDefinition,
    status_code=status.HTTP_201_CREATED,
)
async def create_catalog_store(
    catalog_store: CatalogStoreDefinition = Body(...),
):
    """
    Creates a new catalog store configuration.

    Args:
        catalog_store: The Catalog Store Definition for the store to be created.

    Returns:
        The complete Catalog Store Definition of the newly created store.

    Raises:
        HTTPException: 400 Bad Request if the request body is malformed or missing required fields.
        HTTPException: 409 Conflict if a catalog store with the provided name already exists.
        HTTPException: 500 Internal Server Error if there's an issue persisting the configuration.
    """
    logger.info(f"Creating new catalog store: {catalog_store.name}")
    try:
        created_store = await get_service_manager().catalogstore.create(catalog_store)
        logger.info(f"Successfully created catalog store: {created_store.name}")
        logger.debug(f"Catalog store details: {created_store}")

        return Response(
            status_code=status.HTTP_201_CREATED,
            headers={"Location": f"/catalogstores/{created_store.name}"},
            content=created_store.json(),
        )
    except HTTPException as he:
        logger.error(f"HTTP error creating catalog store {catalog_store.name}: {str(he)}")
        raise
    except Exception as e:
        logger.error(f"Failed to create catalog store {catalog_store.name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create catalog store: {str(e)}",
        )


@router.delete(
    "/catalogstores/{catalogstore_name}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_catalog_store(
    catalogstore_name: str = Path(..., description="The unique name of the catalog store to delete"),
):
    """
    Deletes a specific catalog store identified by its name.

    Args:
        catalogstore_name: The unique name of the catalog store to delete.

    Returns:
        204 No Content on successful deletion.

    Raises:
        HTTPException: 404 Not Found if no catalog store with the specified name exists.
        HTTPException: 500 Internal Server Error if there's an issue deleting the store.
    """
    logger.info(f"Deleting catalog store: {catalogstore_name}")
    try:
        await get_service_manager().catalogstore.delete(catalogstore_name)
        logger.info(f"Successfully deleted catalog store: {catalogstore_name}")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException as he:
        logger.error(f"HTTP error deleting catalog store {catalogstore_name}: {str(he)}")
        raise
    except Exception as e:
        logger.error(f"Failed to delete catalog store {catalogstore_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete catalog store: {str(e)}",
        )
