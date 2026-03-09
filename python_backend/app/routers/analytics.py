from typing import Any, List

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from ..database import get_db
from ..models import (
    AddTagToMenuItemRequest,
    PushToOrderItemsRequest,
    PullFromOrderItemsRequest,
)
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


# ============ OPERACIONES SIMPLES (count, distinct, etc.) ============
@router.get("/simple/distinct-categories")
async def distinct_categories(db: AsyncIOMotorDatabase = Depends(get_db)) -> dict:
    """Operación DISTINCT simple: obtiene categorías únicas de restaurantes"""
    categories = await db["restaurants"].distinct("category")
    return {"categories": categories, "count": len(categories)}


@router.get("/simple/distinct-menu-categories")
async def distinct_menu_categories(db: AsyncIOMotorDatabase = Depends(get_db)) -> dict:
    """Operación DISTINCT: obtiene categorías únicas de items de menú"""
    categories = await db["menuItems"].distinct("category")
    tags = await db["menuItems"].distinct("tags")
    return {"categories": categories, "tags": tags}


@router.get("/simple/counts-by-status")
async def counts_by_status(db: AsyncIOMotorDatabase = Depends(get_db)) -> dict:
    """Operación COUNT con filtro: cuenta órdenes por estado"""
    pending = await db["orders"].count_documents({"status": "pending"})
    completed = await db["orders"].count_documents({"status": "completed"})
    cancelled = await db["orders"].count_documents({"status": "cancelled"})
    return {"pending": pending, "completed": completed, "cancelled": cancelled}


# ============ OPERACIONES COMPLEJAS (pipelines avanzados) ============
@router.get("/complex/user-spending-brackets")
async def user_spending_brackets(db: AsyncIOMotorDatabase = Depends(get_db)) -> List[dict]:
    """Pipeline complejo: agrupa usuarios por rango de gasto con $bucket"""
    pipeline = [
        {
            "$lookup": {
                "from": "orders",
                "localField": "_id",
                "foreignField": "userId",
                "as": "userOrders",
            }
        },
        {
            "$addFields": {
                "totalSpent": {"$sum": "$userOrders.totalAmount"},
            }
        },
        {
            "$bucket": {
                "groupBy": "$totalSpent",
                "boundaries": [0, 500, 1000, 2000, 5000, 10000],
                "default": "high",
                "output": {
                    "count": {"$sum": 1},
                    "users": {
                        "$push": {
                            "userId": "$_id",
                            "name": "$name",
                            "spending": "$totalSpent",
                        }
                    },
                },
            }
        },
        {"$sort": {"_id": 1}},
    ]
    cursor = db["users"].aggregate(pipeline)
    results = await cursor.to_list(length=100)
    return serialize_mongo(results)


@router.get("/complex/restaurant-performance-analytics")
async def restaurant_performance(db: AsyncIOMotorDatabase = Depends(get_db)) -> List[dict]:
    """Pipeline complejo con $facet: múltiples análisis de restaurantes simultáneamente"""
    pipeline = [
        {
            "$facet": {
                "topByRating": [
                    {
                        "$lookup": {
                            "from": "reviews",
                            "localField": "_id",
                            "foreignField": "restaurantId",
                            "as": "reviews",
                        }
                    },
                    {
                        "$addFields": {
                            "avgRating": {"$avg": "$reviews.rating"},
                            "reviewCount": {"$size": "$reviews"},
                        }
                    },
                    {"$sort": {"avgRating": -1}},
                    {"$limit": 5},
                    {
                        "$project": {
                            "name": 1,
                            "category": 1,
                            "avgRating": 1,
                            "reviewCount": 1,
                        }
                    },
                ],
                "topByOrders": [
                    {
                        "$lookup": {
                            "from": "orders",
                            "localField": "_id",
                            "foreignField": "restaurantId",
                            "as": "orders",
                        }
                    },
                    {
                        "$addFields": {
                            "orderCount": {"$size": "$orders"},
                            "totalRevenue": {"$sum": "$orders.totalAmount"},
                        }
                    },
                    {"$sort": {"orderCount": -1}},
                    {"$limit": 5},
                    {
                        "$project": {
                            "name": 1,
                            "orderCount": 1,
                            "totalRevenue": 1,
                        }
                    },
                ],
                "categoryStats": [
                    {
                        "$group": {
                            "_id": "$category",
                            "count": {"$sum": 1},
                            "avgRating": {"$avg": "$ratingAverage"},
                        }
                    },
                    {"$sort": {"count": -1}},
                ],
            }
        }
    ]
    cursor = db["restaurants"].aggregate(pipeline)
    results = await cursor.to_list(length=100)
    return serialize_mongo(results)


@router.get("/complex/order-items-analysis")
async def order_items_analysis(db: AsyncIOMotorDatabase = Depends(get_db)) -> List[dict]:
    """Pipeline complejo: analiza items en documentos embebidos dentro de órdenes"""
    pipeline = [
        {"$unwind": "$items"},
        {
            "$group": {
                "_id": {
                    "itemName": "$items.name",
                    "restaurantId": "$restaurantId",
                },
                "totalQuantity": {"$sum": "$items.quantity"},
                "avgPrice": {"$avg": "$items.price"},
                "maxPrice": {"$max": "$items.price"},
                "totalOrders": {"$sum": 1},
            }
        },
        {"$sort": {"totalQuantity": -1}},
        {"$limit": 20},
        {
            "$lookup": {
                "from": "restaurants",
                "localField": "_id.restaurantId",
                "foreignField": "_id",
                "as": "restaurantInfo",
            }
        },
    ]
    cursor = db["orders"].aggregate(pipeline)
    results = await cursor.to_list(length=100)
    return serialize_mongo(results)


# ============ MANEJO DE ARRAYS - UPDATE OPERATIONS ============
@router.post("/arrays/add-tag-to-menu-item")
async def add_tag_to_menu_item(
    req: AddTagToMenuItemRequest, db: AsyncIOMotorDatabase = Depends(get_db)
) -> dict:
    """$addToSet: Agrega dinámicamente un tag a un item de menú (no duplicados)"""
    try:
        item_id = ObjectId(req.itemId)
    except Exception:
        return {"error": "Invalid item ID format"}

    menu_item = await db["menuItems"].find_one({"_id": item_id})
    if not menu_item:
        return {"error": f"Menu item with ID {req.itemId} not found"}

    result = await db["menuItems"].update_one(
        {"_id": item_id}, {"$addToSet": {"tags": req.tag}}
    )

    updated_item = await db["menuItems"].find_one({"_id": item_id})
    return {
        "action": "$addToSet",
        "description": f"Agregó tag '{req.tag}' si no existe",
        "itemId": req.itemId,
        "modified": result.modified_count,
        "tags": updated_item.get("tags", []),
    }


@router.post("/arrays/push-to-order-items")
async def push_to_order_items(
    req: PushToOrderItemsRequest, db: AsyncIOMotorDatabase = Depends(get_db)
) -> dict:
    """$push: Agrega dinámicamente un item a una orden"""
    try:
        order_id = ObjectId(req.orderId)
    except Exception:
        return {"error": "Invalid order ID format"}

    order = await db["orders"].find_one({"_id": order_id})
    if not order:
        return {"error": f"Order with ID {req.orderId} not found"}

    # Convertir el OrderItem a diccionario
    new_item_dict = req.newItem.model_dump()

    result = await db["orders"].update_one(
        {"_id": order_id}, {"$push": {"items": new_item_dict}}
    )

    updated_order = await db["orders"].find_one({"_id": order_id})
    return {
        "action": "$push",
        "description": "Agregó nuevo item a la orden",
        "orderId": req.orderId,
        "modified": result.modified_count,
        "itemCount": len(updated_order.get("items", [])),
        "items": updated_order.get("items", []),
    }


@router.post("/arrays/pull-from-order-items")
async def pull_from_order_items(
    req: PullFromOrderItemsRequest, db: AsyncIOMotorDatabase = Depends(get_db)
) -> dict:
    """$pull: Remueve dinámicamente items de una orden que cumplan una condición"""
    try:
        order_id = ObjectId(req.orderId)
    except Exception:
        return {"error": "Invalid order ID format"}

    order = await db["orders"].find_one({"_id": order_id})
    if not order:
        return {"error": f"Order with ID {req.orderId} not found"}

    result = await db["orders"].update_one(
        {"_id": order_id}, {"$pull": {"items": req.condition}}
    )

    updated_order = await db["orders"].find_one({"_id": order_id})
    return {
        "action": "$pull",
        "description": f"Eliminó items que cumplan la condición: {req.condition}",
        "orderId": req.orderId,
        "modified": result.modified_count,
        "itemCount": len(updated_order.get("items", [])),
    }


# ============ MANEJO DE DOCUMENTOS EMBEBIDOS ============
@router.get("/embedded/orders-with-enriched-items")
async def orders_with_enriched_items(db: AsyncIOMotorDatabase = Depends(get_db)) -> List[dict]:
    """Operación con documentos embebidos: obtiene órdenes con información enriquecida de items"""
    pipeline = [
        {"$limit": 10},
        {
            "$addFields": {
                "itemsWithUrl": {
                    "$map": {
                        "input": "$items",
                        "as": "item",
                        "in": {
                            "_id": "$$item.menuItemId",
                            "name": "$$item.name",
                            "quantity": "$$item.quantity",
                            "price": "$$item.price",
                            "subtotal": {
                                "$multiply": ["$$item.quantity", "$$item.price"]
                            },
                        },
                    }
                }
            }
        },
        {
            "$project": {
                "_id": 1,
                "userId": 1,
                "restaurantId": 1,
                "createdAt": 1,
                "status": 1,
                "totalAmount": 1,
                "itemsCount": {"$size": "$items"},
                "enrichedItems": "$itemsWithUrl",
            }
        },
    ]
    cursor = db["orders"].aggregate(pipeline)
    results = await cursor.to_list(length=100)
    return serialize_mongo(results)


@router.get("/embedded/restaurant-menu-aggregated")
async def restaurant_menu_aggregated(db: AsyncIOMotorDatabase = Depends(get_db)) -> List[dict]:
    """Documento embebido: restaurantes con su menú agregado"""
    pipeline = [
        {
            "$lookup": {
                "from": "menuItems",
                "localField": "_id",
                "foreignField": "restaurantId",
                "as": "menu",
            }
        },
        {
            "$addFields": {
                "menuCount": {"$size": "$menu"},
                "avgPrice": {"$avg": "$menu.price"},
                "categories": {"$setUnion": ["$menu.category"]},  # Categorías únicas del menú
            }
        },
        {
            "$project": {
                "_id": 1,
                "name": 1,
                "category": 1,
                "menuCount": 1,
                "avgPrice": 1,
                "categories": 1,
                "menu": {
                    "$slice": ["$menu", 5],  # Limitar a 5 items
                },
            }
        },
        {"$limit": 10},
    ]
    cursor = db["restaurants"].aggregate(pipeline)
    results = await cursor.to_list(length=100)
    return serialize_mongo(results)

