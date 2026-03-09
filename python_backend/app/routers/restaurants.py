from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..database import get_db
from ..models import RestaurantCreate, RestaurantPublic, UpdateManyRequest, DeleteManyRequest
from ..services.explain import assert_find_uses_index
from ..utils.mongo import serialize_mongo, to_object_id


router = APIRouter(prefix="/restaurants", tags=["restaurants"])


@router.post("", response_model=RestaurantPublic, status_code=status.HTTP_201_CREATED)
async def create_restaurant(
    restaurant: RestaurantCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = {
        **restaurant.model_dump(),
        "ratingAverage": 0.0,
        "createdAt": datetime.utcnow(),
    }
    result = await db["restaurants"].insert_one(doc)
    saved = await db["restaurants"].find_one({"_id": result.inserted_id})
    if not saved:
        raise HTTPException(status_code=500, detail="Error creating restaurant")
    saved = serialize_mongo(saved)
    return RestaurantPublic(
        id=saved["_id"],
        name=saved["name"],
        description=saved["description"],
        category=saved["category"],
        location=saved["location"],
        ratingAverage=saved.get("ratingAverage", 0.0),
        createdAt=saved["createdAt"],
    )


@router.post("/bulk")
async def create_restaurants_bulk(
    restaurants: List[RestaurantCreate],
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    docs = [
        {
            **r.model_dump(),
            "ratingAverage": 0.0,
            "createdAt": datetime.utcnow(),
        }
        for r in restaurants
    ]
    result = await db["restaurants"].insert_many(docs)
    return {"inserted": len(result.inserted_ids)}


@router.get("", response_model=List[RestaurantPublic])
async def list_restaurants(
    category: Optional[str] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=200),
    sort: str = Query(default="-createdAt", description="e.g. createdAt or -createdAt"),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    query = {}
    if category:
        query["category"] = category

    sort_field = sort.lstrip("-")
    sort_dir = -1 if sort.startswith("-") else 1

    cursor = (
        db["restaurants"]
        .find(query)
        .sort(sort_field, sort_dir)
        .skip(skip)
        .limit(limit)
    )

    out: list[RestaurantPublic] = []
    async for doc in cursor:
        doc = serialize_mongo(doc)
        out.append(
            RestaurantPublic(
                id=doc["_id"],
                name=doc["name"],
                description=doc["description"],
                category=doc["category"],
                location=doc["location"],
                ratingAverage=doc.get("ratingAverage", 0.0),
                createdAt=doc["createdAt"],
            )
        )
    return out


@router.get("/search", response_model=List[RestaurantPublic])
async def search_restaurants(
    q: str,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=200),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    query = {"$text": {"$search": q}}
    await assert_find_uses_index(db, "restaurants", query, skip=skip, limit=limit)
    cursor = db["restaurants"].find(query).skip(skip).limit(limit)
    out: list[RestaurantPublic] = []
    async for doc in cursor:
        doc = serialize_mongo(doc)
        out.append(
            RestaurantPublic(
                id=doc["_id"],
                name=doc["name"],
                description=doc["description"],
                category=doc["category"],
                location=doc["location"],
                ratingAverage=doc.get("ratingAverage", 0.0),
                createdAt=doc["createdAt"],
            )
        )
    return out


@router.get("/near", response_model=List[RestaurantPublic])
async def restaurants_near(
    lng: float,
    lat: float,
    maxDistance: int = Query(default=5000, ge=1),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=200),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    query = {
        "location": {
            "$near": {
                "$geometry": {"type": "Point", "coordinates": [lng, lat]},
                "$maxDistance": maxDistance,
            }
        }
    }
    await assert_find_uses_index(db, "restaurants", query, skip=skip, limit=limit)
    cursor = db["restaurants"].find(query).skip(skip).limit(limit)
    out: list[RestaurantPublic] = []
    async for doc in cursor:
        doc = serialize_mongo(doc)
        out.append(
            RestaurantPublic(
                id=doc["_id"],
                name=doc["name"],
                description=doc["description"],
                category=doc["category"],
                location=doc["location"],
                ratingAverage=doc.get("ratingAverage", 0.0),
                createdAt=doc["createdAt"],
            )
        )
    return out


@router.get("/{restaurant_id}", response_model=RestaurantPublic)
async def get_restaurant(
    restaurant_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db["restaurants"].find_one({"_id": to_object_id(restaurant_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    doc = serialize_mongo(doc)
    return RestaurantPublic(
        id=doc["_id"],
        name=doc["name"],
        description=doc["description"],
        category=doc["category"],
        location=doc["location"],
        ratingAverage=doc.get("ratingAverage", 0.0),
        createdAt=doc["createdAt"],
    )


@router.patch("/{restaurant_id}")
async def update_restaurant(
    restaurant_id: str,
    patch: dict,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    result = await db["restaurants"].update_one(
        {"_id": to_object_id(restaurant_id)},
        {"$set": patch},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return {"matched": result.matched_count, "modified": result.modified_count}


@router.patch("/bulk/update-many")
async def update_restaurants_many(
    req: UpdateManyRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    result = await db["restaurants"].update_many(req.filter, req.update)
    return {"matched": result.matched_count, "modified": result.modified_count}


@router.delete("/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_restaurant(
    restaurant_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    await db["restaurants"].delete_one({"_id": to_object_id(restaurant_id)})
    return None


@router.post("/bulk/delete-many")
async def delete_restaurants_many(
    req: DeleteManyRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    result = await db["restaurants"].delete_many(req.filter)
    return {"deleted": result.deleted_count}

