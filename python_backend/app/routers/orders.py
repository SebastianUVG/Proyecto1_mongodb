from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..database import client, get_db
from ..models import (
    CreateOrderWithOptionalReviewRequest,
    DeleteManyRequest,
    OrderItem,
    OrderPublic,
    OrderCreateRequest,
    UpdateManyRequest,
)
from ..services.explain import assert_find_uses_index
from ..utils.mongo import serialize_mongo, to_object_id


router = APIRouter(prefix="/orders", tags=["orders"])


def _calc_total(items: List[OrderItem]) -> float:
    return float(sum(i.price * i.quantity for i in items))


@router.post("", response_model=OrderPublic, status_code=status.HTTP_201_CREATED)
async def create_order(
    order: OrderCreateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    total_amount = _calc_total(order.items)
    doc = {
        "userId": to_object_id(order.userId),
        "restaurantId": to_object_id(order.restaurantId),
        "items": [
            {
                "menuItemId": to_object_id(i.menuItemId),
                "name": i.name,
                "quantity": i.quantity,
                "price": i.price,
            }
            for i in order.items
        ],
        "status": order.status,
        "totalAmount": total_amount,
        "createdAt": datetime.utcnow(),
    }
    result = await db["orders"].insert_one(doc)
    saved = await db["orders"].find_one({"_id": result.inserted_id})
    if not saved:
        raise HTTPException(status_code=500, detail="Error creating order")
    saved = serialize_mongo(saved)
    return OrderPublic(
        id=saved["_id"],
        userId=saved["userId"],
        restaurantId=saved["restaurantId"],
        items=[
            OrderItem(
                menuItemId=i["menuItemId"],
                name=i["name"],
                quantity=i["quantity"],
                price=i["price"],
            )
            for i in saved["items"]
        ],
        status=saved["status"],
        totalAmount=saved["totalAmount"],
        createdAt=saved["createdAt"],
    )


@router.post("/bulk")
async def create_orders_bulk(
    orders: List[OrderCreateRequest],
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    docs = []
    for o in orders:
        docs.append(
            {
                "userId": to_object_id(o.userId),
                "restaurantId": to_object_id(o.restaurantId),
                "items": [
                    {
                        "menuItemId": to_object_id(i.menuItemId),
                        "name": i.name,
                        "quantity": i.quantity,
                        "price": i.price,
                    }
                    for i in o.items
                ],
                "status": o.status,
                "totalAmount": _calc_total(o.items),
                "createdAt": datetime.utcnow(),
            }
        )
    result = await db["orders"].insert_many(docs)
    return {"inserted": len(result.inserted_ids)}


@router.post("/with-review", response_model=OrderPublic, status_code=status.HTTP_201_CREATED)
async def create_order_with_optional_review(
    req: CreateOrderWithOptionalReviewRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    order = req.order
    review = req.review
    total_amount = _calc_total(order.items)

    async with await client.start_session() as session:
        async with session.start_transaction():
            order_doc = {
                "userId": to_object_id(order.userId),
                "restaurantId": to_object_id(order.restaurantId),
                "items": [
                    {
                        "menuItemId": to_object_id(i.menuItemId),
                        "name": i.name,
                        "quantity": i.quantity,
                        "price": i.price,
                    }
                    for i in order.items
                ],
                "status": order.status,
                "totalAmount": total_amount,
                "createdAt": datetime.utcnow(),
            }
            order_result = await db["orders"].insert_one(order_doc, session=session)

            if review:
                review_doc = {
                    "restaurantId": to_object_id(order.restaurantId),
                    "userId": to_object_id(order.userId),
                    "orderId": order_result.inserted_id,
                    "rating": review.rating,
                    "comment": review.comment,
                    "createdAt": datetime.utcnow(),
                }
                await db["reviews"].insert_one(review_doc, session=session)

    saved = await db["orders"].find_one({"_id": order_result.inserted_id})
    if not saved:
        raise HTTPException(status_code=500, detail="Error creating order")
    saved = serialize_mongo(saved)
    return OrderPublic(
        id=saved["_id"],
        userId=saved["userId"],
        restaurantId=saved["restaurantId"],
        items=[
            OrderItem(
                menuItemId=i["menuItemId"],
                name=i["name"],
                quantity=i["quantity"],
                price=i["price"],
            )
            for i in saved["items"]
        ],
        status=saved["status"],
        totalAmount=saved["totalAmount"],
        createdAt=saved["createdAt"],
    )


@router.get("/by-restaurant/{restaurant_id}")
async def list_orders_by_restaurant(
    restaurant_id: str,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=200),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    filt = {"restaurantId": to_object_id(restaurant_id)}
    sort = {"createdAt": -1}
    await assert_find_uses_index(db, "orders", filt, sort=sort, skip=skip, limit=limit)
    cursor = db["orders"].find(filt).sort("createdAt", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    return serialize_mongo(docs)


@router.get("/{order_id}", response_model=OrderPublic)
async def get_order(order_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    doc = await db["orders"].find_one({"_id": to_object_id(order_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Order not found")
    doc = serialize_mongo(doc)
    return OrderPublic(
        id=doc["_id"],
        userId=doc["userId"],
        restaurantId=doc["restaurantId"],
        items=[
            OrderItem(
                menuItemId=i["menuItemId"],
                name=i["name"],
                quantity=i["quantity"],
                price=i["price"],
            )
            for i in doc["items"]
        ],
        status=doc["status"],
        totalAmount=doc["totalAmount"],
        createdAt=doc["createdAt"],
    )


@router.post("/{order_id}/items:push")
async def push_order_item(
    order_id: str,
    item: OrderItem,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    await db["orders"].update_one(
        {"_id": to_object_id(order_id)},
        {
            "$push": {
                "items": {
                    "menuItemId": to_object_id(item.menuItemId),
                    "name": item.name,
                    "quantity": item.quantity,
                    "price": item.price,
                }
            }
        },
    )
    updated = await db["orders"].find_one({"_id": to_object_id(order_id)})
    if not updated:
        raise HTTPException(status_code=404, detail="Order not found")
    total = float(
        sum(i["price"] * i["quantity"] for i in updated.get("items", []))
    )
    await db["orders"].update_one(
        {"_id": to_object_id(order_id)},
        {"$set": {"totalAmount": total}},
    )
    return {"ok": True, "totalAmount": total}


@router.post("/{order_id}/items:pull")
async def pull_order_item(
    order_id: str,
    menuItemId: str = Body(..., embed=True),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    await db["orders"].update_one(
        {"_id": to_object_id(order_id)},
        {"$pull": {"items": {"menuItemId": to_object_id(menuItemId)}}},
    )
    updated = await db["orders"].find_one({"_id": to_object_id(order_id)})
    if not updated:
        raise HTTPException(status_code=404, detail="Order not found")
    total = float(
        sum(i["price"] * i["quantity"] for i in updated.get("items", []))
    )
    await db["orders"].update_one(
        {"_id": to_object_id(order_id)},
        {"$set": {"totalAmount": total}},
    )
    return {"ok": True, "totalAmount": total}


@router.get("")
async def list_orders(
    restaurantId: Optional[str] = None,
    userId: Optional[str] = None,
    status_: Optional[str] = Query(default=None, alias="status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=200),
    sort: str = Query(default="-createdAt"),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    query: dict[str, Any] = {}
    if restaurantId:
        query["restaurantId"] = to_object_id(restaurantId)
    if userId:
        query["userId"] = to_object_id(userId)
    if status_:
        query["status"] = status_

    sort_field = sort.lstrip("-")
    sort_dir = -1 if sort.startswith("-") else 1

    cursor = (
        db["orders"]
        .find(query)
        .sort(sort_field, sort_dir)
        .skip(skip)
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)
    return serialize_mongo(docs)


@router.get("/enriched/query")
async def list_orders_enriched(
    restaurantId: Optional[str] = None,
    status_: Optional[str] = Query(default=None, alias="status"),
    minTotal: Optional[float] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=200),
    sort: str = Query(default="-createdAt"),
    lite: bool = Query(default=False, description="If true, return fewer fields"),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    match: dict[str, Any] = {}
    if restaurantId:
        match["restaurantId"] = to_object_id(restaurantId)
    if status_:
        match["status"] = status_
    if minTotal is not None:
        match["totalAmount"] = {"$gte": minTotal}

    sort_field = sort.lstrip("-")
    sort_dir = -1 if sort.startswith("-") else 1

    pipeline: list[dict] = []
    if match:
        pipeline.append({"$match": match})

    pipeline.extend(
        [
            {"$sort": {sort_field: sort_dir}},
            {"$skip": skip},
            {"$limit": limit},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "userId",
                    "foreignField": "_id",
                    "as": "user",
                }
            },
            {
                "$lookup": {
                    "from": "restaurants",
                    "localField": "restaurantId",
                    "foreignField": "_id",
                    "as": "restaurant",
                }
            },
        ]
    )

    if lite:
        pipeline.append(
            {
                "$project": {
                    "status": 1,
                    "totalAmount": 1,
                    "createdAt": 1,
                    "user": {"$slice": ["$user", 1]},
                    "restaurant": {"$slice": ["$restaurant", 1]},
                }
            }
        )

    cursor = db["orders"].aggregate(pipeline)
    results = await cursor.to_list(length=limit)
    return serialize_mongo(results)


@router.patch("/{order_id}")
async def update_order(order_id: str, patch: dict, db: AsyncIOMotorDatabase = Depends(get_db)):
    result = await db["orders"].update_one({"_id": to_object_id(order_id)}, {"$set": patch})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"matched": result.matched_count, "modified": result.modified_count}


@router.patch("/bulk/update-many")
async def update_orders_many(req: UpdateManyRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    filt = dict(req.filter)
    for k in ("restaurantId", "userId"):
        if k in filt and isinstance(filt[k], str):
            filt[k] = to_object_id(filt[k])
    result = await db["orders"].update_many(filt, req.update)
    return {"matched": result.matched_count, "modified": result.modified_count}


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(order_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    await db["orders"].delete_one({"_id": to_object_id(order_id)})
    return None


@router.post("/bulk/delete-many")
async def delete_orders_many(req: DeleteManyRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    filt = dict(req.filter)
    for k in ("restaurantId", "userId"):
        if k in filt and isinstance(filt[k], str):
            filt[k] = to_object_id(filt[k])
    result = await db["orders"].delete_many(filt)
    return {"deleted": result.deleted_count}

