from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..database import get_db
from ..models import DeleteManyRequest, UpdateManyRequest, UserCreate, UserPublic
from ..services.explain import assert_find_uses_index
from ..utils.mongo import serialize_mongo, to_object_id


router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    doc = {**user.model_dump(), "createdAt": datetime.utcnow()}
    result = await db["users"].insert_one(doc)
    saved = await db["users"].find_one({"_id": result.inserted_id})
    if not saved:
        raise HTTPException(status_code=500, detail="Error creating user")
    saved = serialize_mongo(saved)
    return UserPublic(
        id=saved["_id"],
        name=saved["name"],
        email=saved["email"],
        role=saved["role"],
        createdAt=saved["createdAt"],
    )


@router.post("/bulk")
async def create_users_bulk(users: List[UserCreate], db: AsyncIOMotorDatabase = Depends(get_db)):
    docs = [{**u.model_dump(), "createdAt": datetime.utcnow()} for u in users]
    result = await db["users"].insert_many(docs, ordered=False)
    return {"inserted": len(result.inserted_ids)}


@router.get("", response_model=List[UserPublic])
async def list_users(
    role: Optional[str] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=200),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    query = {}
    if role:
        query["role"] = role
    cursor = db["users"].find(query).skip(skip).limit(limit)
    out: list[UserPublic] = []
    async for doc in cursor:
        doc = serialize_mongo(doc)
        out.append(
            UserPublic(
                id=doc["_id"],
                name=doc["name"],
                email=doc["email"],
                role=doc["role"],
                createdAt=doc["createdAt"],
            )
        )
    return out


@router.get("/by-email", response_model=UserPublic)
async def get_user_by_email(email: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    await assert_find_uses_index(
        db,
        "users",
        {"email": email},
        projection={"password": 0},
        limit=1,
    )
    doc = await db["users"].find_one({"email": email}, projection={"password": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="User not found")
    doc = serialize_mongo(doc)
    return UserPublic(
        id=doc["_id"],
        name=doc["name"],
        email=doc["email"],
        role=doc["role"],
        createdAt=doc["createdAt"],
    )


@router.get("/{user_id}", response_model=UserPublic)
async def get_user(user_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    doc = await db["users"].find_one({"_id": to_object_id(user_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="User not found")
    doc = serialize_mongo(doc)
    return UserPublic(
        id=doc["_id"],
        name=doc["name"],
        email=doc["email"],
        role=doc["role"],
        createdAt=doc["createdAt"],
    )


@router.patch("/{user_id}")
async def update_user(user_id: str, patch: dict, db: AsyncIOMotorDatabase = Depends(get_db)):
    result = await db["users"].update_one({"_id": to_object_id(user_id)}, {"$set": patch})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"matched": result.matched_count, "modified": result.modified_count}


@router.patch("/bulk/update-many")
async def update_users_many(req: UpdateManyRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    result = await db["users"].update_many(req.filter, req.update)
    return {"matched": result.matched_count, "modified": result.modified_count}


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    await db["users"].delete_one({"_id": to_object_id(user_id)})
    return None


@router.post("/bulk/delete-many")
async def delete_users_many(req: DeleteManyRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    result = await db["users"].delete_many(req.filter)
    return {"deleted": result.deleted_count}

