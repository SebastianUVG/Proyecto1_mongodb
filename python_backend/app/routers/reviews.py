from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..database import get_db
from ..models import DeleteManyRequest, ReviewBase, ReviewPublic, UpdateManyRequest
from ..utils.mongo import serialize_mongo, to_object_id


router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("", response_model=ReviewPublic, status_code=status.HTTP_201_CREATED)
async def create_review(review: ReviewBase, db: AsyncIOMotorDatabase = Depends(get_db)):
    doc = {
        "restaurantId": to_object_id(review.restaurantId),
        "userId": to_object_id(review.userId),
        "orderId": to_object_id(review.orderId) if review.orderId else None,
        "rating": review.rating,
        "comment": review.comment,
        "createdAt": datetime.utcnow(),
    }
    result = await db["reviews"].insert_one(doc)
    saved = await db["reviews"].find_one({"_id": result.inserted_id})
    if not saved:
        raise HTTPException(status_code=500, detail="Error creating review")
    saved = serialize_mongo(saved)
    return ReviewPublic(
        id=saved["_id"],
        restaurantId=saved["restaurantId"],
        userId=saved["userId"],
        orderId=saved.get("orderId"),
        rating=saved["rating"],
        comment=saved["comment"],
        createdAt=saved["createdAt"],
    )


@router.post("/bulk")
async def create_reviews_bulk(reviews: List[ReviewBase], db: AsyncIOMotorDatabase = Depends(get_db)):
    docs = []
    for r in reviews:
        docs.append(
            {
                "restaurantId": to_object_id(r.restaurantId),
                "userId": to_object_id(r.userId),
                "orderId": to_object_id(r.orderId) if r.orderId else None,
                "rating": r.rating,
                "comment": r.comment,
                "createdAt": datetime.utcnow(),
            }
        )
    result = await db["reviews"].insert_many(docs)
    return {"inserted": len(result.inserted_ids)}


@router.get("", response_model=List[ReviewPublic])
async def list_reviews(
    restaurantId: Optional[str] = None,
    userId: Optional[str] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=200),
    sort: str = Query(default="-createdAt", description="e.g. rating or -createdAt"),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    query: dict[str, Any] = {}
    if restaurantId:
        query["restaurantId"] = to_object_id(restaurantId)
    if userId:
        query["userId"] = to_object_id(userId)

    sort_field = sort.lstrip("-")
    sort_dir = -1 if sort.startswith("-") else 1

    cursor = (
        db["reviews"]
        .find(query)
        .sort(sort_field, sort_dir)
        .skip(skip)
        .limit(limit)
    )
    out: list[ReviewPublic] = []
    async for doc in cursor:
        doc = serialize_mongo(doc)
        out.append(
            ReviewPublic(
                id=doc["_id"],
                restaurantId=doc["restaurantId"],
                userId=doc["userId"],
                orderId=doc.get("orderId"),
                rating=doc["rating"],
                comment=doc["comment"],
                createdAt=doc["createdAt"],
            )
        )
    return out


@router.get("/{review_id}", response_model=ReviewPublic)
async def get_review(review_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    doc = await db["reviews"].find_one({"_id": to_object_id(review_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Review not found")
    doc = serialize_mongo(doc)
    return ReviewPublic(
        id=doc["_id"],
        restaurantId=doc["restaurantId"],
        userId=doc["userId"],
        orderId=doc.get("orderId"),
        rating=doc["rating"],
        comment=doc["comment"],
        createdAt=doc["createdAt"],
    )


@router.patch("/{review_id}")
async def update_review(review_id: str, patch: dict, db: AsyncIOMotorDatabase = Depends(get_db)):
    if "restaurantId" in patch:
        patch["restaurantId"] = to_object_id(patch["restaurantId"])
    if "userId" in patch:
        patch["userId"] = to_object_id(patch["userId"])
    if "orderId" in patch and patch["orderId"] is not None:
        patch["orderId"] = to_object_id(patch["orderId"])
    result = await db["reviews"].update_one({"_id": to_object_id(review_id)}, {"$set": patch})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Review not found")
    return {"matched": result.matched_count, "modified": result.modified_count}


@router.patch("/bulk/update-many")
async def update_reviews_many(req: UpdateManyRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    filt = dict(req.filter)
    for k in ("restaurantId", "userId", "orderId"):
        if k in filt and isinstance(filt[k], str):
            filt[k] = to_object_id(filt[k])
    result = await db["reviews"].update_many(filt, req.update)
    return {"matched": result.matched_count, "modified": result.modified_count}


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(review_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    await db["reviews"].delete_one({"_id": to_object_id(review_id)})
    return None


@router.post("/bulk/delete-many")
async def delete_reviews_many(req: DeleteManyRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    filt = dict(req.filter)
    for k in ("restaurantId", "userId", "orderId"):
        if k in filt and isinstance(filt[k], str):
            filt[k] = to_object_id(filt[k])
    result = await db["reviews"].delete_many(filt)
    return {"deleted": result.deleted_count}

