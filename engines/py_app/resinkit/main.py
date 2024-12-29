from typing_extensions import Annotated
from fastapi import FastAPI, Depends, HTTPException, Header
from resinkit.api_flink import router as flink_router
from resinkit.api_common import router as common_router  # Add this import

app = FastAPI()


async def verify_token(x_resinkit_token: Annotated[str, Header()]):
    if not x_resinkit_token:
        raise HTTPException(
            status_code=401, detail="X-Resinkit-Token header invalid")


# Include the Flink router with the prefix and dependencies
app.include_router(
    flink_router,
    prefix="/api/v0/flink",
    dependencies=[Depends(verify_token)],
    tags=["flink"]
)

# Include the common router
app.include_router(
    common_router,
    tags=["common"]
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8601)
