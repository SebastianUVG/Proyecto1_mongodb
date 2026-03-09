from typing import Any, List

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..database import get_db
from ..utils.mongo import serialize_mongo


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/top-restaurants")
async def top_rated_restaurants(db: AsyncIOMotorDatabase = Depends(get_db)) -> List[dict]:
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
    cursor = db["reviews"].aggregate(pipeline)
    results = await cursor.to_list(length=100)
    return serialize_mongo(results)


@router.get("/top-menu-items")
async def top_menu_items(db: AsyncIOMotorDatabase = Depends(get_db)) -> List[dict]:
    pipeline = [
        {"$unwind": "$items"},
        {
            "$group": {
                "_id": "$items.name",
                "totalSold": {"$sum": "$items.quantity"},
            }
        },
        {"$sort": {"totalSold": -1}},
        {"$limit": 10},
    ]
    cursor = db["orders"].aggregate(pipeline)
    results = await cursor.to_list(length=100)
    return serialize_mongo(results)


@router.get("/revenue-by-restaurant")
async def revenue_by_restaurant(db: AsyncIOMotorDatabase = Depends(get_db)) -> List[dict]:
    pipeline = [
        {
            "$group": {
                "_id": "$restaurantId",
                "totalRevenue": {"$sum": "$totalAmount"},
                "ordersCount": {"$sum": 1},
            }
        },
        {"$sort": {"totalRevenue": -1}},
        {
            "$lookup": {
                "from": "restaurants",
                "localField": "_id",
                "foreignField": "_id",
                "as": "restaurant",
            }
        },
    ]
    cursor = db["orders"].aggregate(pipeline)
    results = await cursor.to_list(length=500)
    return serialize_mongo(results)


@router.get("/counts")
async def simple_counts(db: AsyncIOMotorDatabase = Depends(get_db)) -> dict:
    return {
        "restaurants": await db["restaurants"].count_documents({}),
        "users": await db["users"].count_documents({}),
        "menuItems": await db["menuItems"].count_documents({}),
        "orders": await db["orders"].count_documents({}),
        "reviews": await db["reviews"].count_documents({}),
    }

