from datetime import datetime
from typing import Any, List, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorGridFSBucket

from ..database import get_db
from ..utils.mongo import serialize_mongo, to_object_id


router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    bucket = AsyncIOMotorGridFSBucket(db)
    try:
        grid_id = await bucket.upload_from_stream(
            file.filename,
            file.file,
            metadata={
                "contentType": file.content_type,
                "uploadedAt": datetime.utcnow(),
            },
        )
    finally:
        await file.close()

    meta = {
        "gridfsId": grid_id,
        "filename": file.filename,
        "contentType": file.content_type,
        "uploadedAt": datetime.utcnow(),
    }
    result = await db["files"].insert_one(meta)
    return {"id": str(result.inserted_id), "gridfsId": str(grid_id), "filename": file.filename}


@router.get("")
async def list_files(db: AsyncIOMotorDatabase = Depends(get_db)) -> List[dict]:
    cursor = db["files"].find().sort("uploadedAt", -1).limit(200)
    docs = await cursor.to_list(length=200)
    return serialize_mongo(docs)


@router.get("/{gridfs_id}")
async def download_file(
    gridfs_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    bucket = AsyncIOMotorGridFSBucket(db)
    oid = to_object_id(gridfs_id)

    try:
        grid_out = await bucket.open_download_stream(oid)
    except Exception:
        raise HTTPException(status_code=404, detail="File not found in GridFS")

    async def file_iterator():
        while True:
            chunk = await grid_out.readchunk()
            if not chunk:
                break
            yield chunk

    content_type = None
    try:
        if grid_out.metadata:
            content_type = grid_out.metadata.get("contentType")
    except Exception:
        content_type = None

    return StreamingResponse(
        file_iterator(),
        media_type=content_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{grid_out.filename}"'},
    )

