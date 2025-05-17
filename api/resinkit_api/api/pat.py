from fastapi import APIRouter, Header, HTTPException
from typing import Optional
from resinkit_api.core.config import settings
import httpx
import json
from resinkit_api.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/validate")
async def validate(x_resinkit_pat: Optional[str] = Header(None, alias="x-resinkit-pat"), authorization: Optional[str] = Header(None)):
    # Check x-resinkit-pat header first, then fall back to authorization header
    pat = x_resinkit_pat or authorization
    logger.info(f"PAT: {pat}")

    if not pat:
        raise HTTPException(status_code=401, detail="Authorization failed")

    if settings.IS_BYOC and settings.X_RESINKIT_PAT:
        logger.info(f"BYOC: {settings.X_RESINKIT_PAT}")
        if pat != settings.X_RESINKIT_PAT:
            raise HTTPException(status_code=401, detail="Authorization failed")
        return {"permissions": "*"}

    # Call resink.ai to validate PAT
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://resink.ai/api/pat/validate", json={"token": pat}, headers={"accept": "application/json", "Content-Type": "application/json"}
            )
            logger.info(f"PAT validation response: {response.json()}")
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Authorization failed")

            result = response.json()
            if not result.get("valid", False):
                raise HTTPException(status_code=401, detail="Authorization failed")

            # Return the permissions from the API response
            return {"permissions": result.get("permissions", [])}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error validating PAT: {str(e)}")
