from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing_extensions import Annotated

from resinkit_api.api.catalogstore import router as catalogstore_router
from resinkit_api.api.catalog import router as catalog_router
from resinkit_api.api.health import router as health_router
from resinkit_api.api.flink import router as flink_router
from resinkit_api.api.agent import router as agent_router
from resinkit_api.api.pat import router as authorization_router

from resinkit_api.core.logging import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting lifespan")
    # Create database tables (if not using Alembic migrations for development)
    # Base.metadata.create_all(bind=engine)
    yield
    logger.info("Ending lifespan")


app = FastAPI(
    title="Resinkit API",
    description="Service for interacting with Resinkit",
    version="0.1.0",
    contact={
        "name": "Resinkit",
        "url": "https://resink.ai",
        "email": "support@resink.ai",
    },
    lifespan=lifespan,
)

# Add the security scheme to the OpenAPI components
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def verify_token(x_resinkit_api_token: Annotated[str, Header()]):
    if not x_resinkit_api_token:
        raise HTTPException(status_code=401, detail="X-ResinKit-Api-Token header invalid")


# Include the Flink router with the prefix and dependencies
app.include_router(
    flink_router,
    prefix="/api/v1/flink",
    tags=["flink"],
)

# Include the catalogstore router
app.include_router(
    catalogstore_router,
    prefix="/api/v1",
    tags=["catalog"],
)

# Include the catalog router
app.include_router(
    catalog_router,
    prefix="/api/v1",
    tags=["catalog"],
)

# Include the health router
app.include_router(health_router, tags=["health"])

# Include the authorization router
app.include_router(authorization_router, prefix="/api/v1/pat", tags=["common"])

# Include the agent router
app.include_router(
    agent_router,
    prefix="/api/v1/agent",
    tags=["agent"],
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8602)
