from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from fastapi import Depends, FastAPI, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from .database import create_indexes, db, get_db, client
from .models import (
    OrderCreate,
    OrderItem,
    OrderPublic,
    RestaurantCreate,
    RestaurantInDB,
    RestaurantPublic,
    TopRatedRestaurant,
)


app = FastAPI(title="Restaurant System API - Python/FastAPI")


@app.on_event("startup")
async def on_startup() -> None:
    await create_indexes()


def _object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ObjectId format",
        )


@app.post("/restaurants", response_model=RestaurantPublic, status_code=status.HTTP_201_CREATED)
async def create_restaurant(
    restaurant: RestaurantCreate,
    database: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = {
        **restaurant.model_dict(),
        "ratingAverage": 0.0,
        "createdAt": datetime.utcnow(),
    }
    result = await database["restaurants"].insert_one(doc)
    saved = await database["restaurants"].find_one({"_id": result.inserted_id})
    if not saved:
        raise HTTPException(status_code=500, detail="Error creating restaurant")
    return RestaurantPublic(
        id=str(saved["_id"]),
        name=saved["name"],
        description=saved["description"],
        category=saved["category"],
        location=saved["location"],
        ratingAverage=saved["ratingAverage"],
        createdAt=saved["createdAt"],
    )


@app.get("/restaurants", response_model=List[RestaurantPublic])
async def list_restaurants(
    database: AsyncIOMotorDatabase = Depends(get_db),
):
    cursor = database["restaurants"].find()
    restaurants: list[RestaurantPublic] = []
    async for doc in cursor:
        restaurants.append(
            RestaurantPublic(
                id=str(doc["_id"]),
                name=doc["name"],
                description=doc["description"],
                category=doc["category"],
                location=doc["location"],
                ratingAverage=doc.get("ratingAverage", 0.0),
                createdAt=doc["createdAt"],
            )
        )
    return restaurants


@app.post("/orders", response_model=OrderPublic, status_code=status.HTTP_201_CREATED)
async def create_order_with_optional_review(
    order: OrderCreate,
    review: Optional[dict] = None,
    database: AsyncIOMotorDatabase = Depends(get_db),
):
    # Calcula el total igual que en Node
    total_amount = sum(
        item.price * item.quantity for item in order.items
    )

    async with await client.start_session() as session:
        async with session.start_transaction():
            orders_coll = database["orders"]
            reviews_coll = database["reviews"]

            order_doc = {
                "userId": _object_id(order.userId),
                "restaurantId": _object_id(order.restaurantId),
                "items": [
                    {
                        "menuItemId": _object_id(i.menuItemId),
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

            order_result = await orders_coll.insert_one(order_doc, session=session)

            if review:
                review_doc = {
                    "restaurantId": _object_id(order.restaurantId),
                    "userId": _object_id(order.userId),
                    "orderId": order_result.inserted_id,
                    "rating": review["rating"],
                    "comment": review.get("comment", ""),
                    "createdAt": datetime.utcnow(),
                }
                await reviews_coll.insert_one(review_doc, session=session)

    saved = await database["orders"].find_one({"_id": order_result.inserted_id})
    if not saved:
        raise HTTPException(status_code=500, detail="Error creating order")

    return OrderPublic(
        id=str(saved["_id"]),
        userId=str(saved["userId"]),
        restaurantId=str(saved["restaurantId"]),
        items=[
            OrderItem(
                menuItemId=str(i["menuItemId"]),
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


@app.get("/analytics/top-restaurants", response_model=List[TopRatedRestaurant])
async def top_rated_restaurants(
    database: AsyncIOMotorDatabase = Depends(get_db),
):
    pipeline = [
        {
            "$group": {
                "_id": "$restaurantId",
                "avgRating": {"$avg": "$rating"},
                "totalReviews": {"$sum": 1},
            }
        },
        {"$sort": {"avgRating": -1}},
        {"$limit": 5},
        {
            "$lookup": {
                "from": "restaurants",
                "localField": "_id",
                "foreignField": "_id",
                "as": "restaurant",
            }
        },
    ]

    cursor = database["reviews"].aggregate(pipeline)
    results = await cursor.to_list(length=100)
    # Serializar ObjectId a str
    for r in results:
        r["_id"] = str(r["_id"])
    return results

