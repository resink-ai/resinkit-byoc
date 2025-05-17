from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from typing import Optional
import httpx
import os
import shutil
from resinkit_api.core.config import settings
from resinkit_api.api.models.models_flink import SQLQuery

router = APIRouter()


# Pre-configured name to URL map
NAME_TO_URL = {
    "MySQL Pipeline Connector 3.2.0": "https://repo1.maven.org/maven2/org/apache/flink/flink-cdc-pipeline-connector-mysql/3.2.0/flink-cdc-pipeline-connector-mysql-3.2.0.jar"
}


@router.put("/lib/download")
async def download_jar(name: Optional[str] = None, url: Optional[str] = None):
    if name and name in NAME_TO_URL:
        url = NAME_TO_URL[name]
    elif not url:
        raise HTTPException(status_code=400, detail="Either name or url must be provided")

    filename = url.split("/")[-1]
    filepath = os.path.join(settings.FLINK_LIB_DIR, filename)

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to download the jar file")

        with open(filepath, "wb") as f:
            f.write(response.content)

    return {"message": f"Successfully downloaded and saved {filename} to {settings.FLINK_LIB_DIR}"}


@router.post("/lib/upload")
async def upload_jar(file: UploadFile = File(...), filename: str = Form(...)):
    filepath = os.path.join(settings.FLINK_LIB_DIR, filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"message": f"Successfully uploaded {filename} to {settings.FLINK_LIB_DIR}"}


@router.post("/runsql")
async def run_sql(query: SQLQuery):
    # Implement your Flink SQL execution logic here
    # This is a placeholder implementation
    return {"message": "SQL execution not implemented", "sql": query.sql}
