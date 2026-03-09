from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..database import get_db
from ..models import (
    DeleteManyRequest,
    MenuItemCreate,
    MenuItemPublic,
    UpdateManyRequest,
)
from ..services.explain import assert_find_uses_index
from ..utils.mongo import serialize_mongo, to_object_id


router = APIRouter(prefix="/menu-items", tags=["menuItems"])


@router.post("", response_model=MenuItemPublic, status_code=status.HTTP_201_CREATED)
async def create_menu_item(item: MenuItemCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    doc = {**item.model_dump(), "restaurantId": to_object_id(item.restaurantId)}
    result = await db["menuItems"].insert_one(doc)
    saved = await db["menuItems"].find_one({"_id": result.inserted_id})
    if not saved:
        raise HTTPException(status_code=500, detail="Error creating menu item")
    saved = serialize_mongo(saved)
    return MenuItemPublic(**{**saved, "id": saved["_id"], "restaurantId": saved["restaurantId"]})


@router.post("/bulk")
async def create_menu_items_bulk(items: List[MenuItemCreate], db: AsyncIOMotorDatabase = Depends(get_db)):
    docs = [
        {**i.model_dump(), "restaurantId": to_object_id(i.restaurantId)}
        for i in items
    ]
    result = await db["menuItems"].insert_many(docs)
    return {"inserted": len(result.inserted_ids)}


@router.get("", response_model=List[MenuItemPublic])
async def list_menu_items(
    restaurantId: Optional[str] = None,
    tag: Optional[str] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=200),
    sort: str = Query(default="price"),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    query: dict = {}
    if restaurantId:
        query["restaurantId"] = to_object_id(restaurantId)
    if tag:
        query["tags"] = tag

    sort_field = sort.lstrip("-")
    sort_dir = -1 if sort.startswith("-") else 1

    cursor = (
        db["menuItems"]
        .find(query)
        .sort(sort_field, sort_dir)
        .skip(skip)
        .limit(limit)
    )
    out: list[MenuItemPublic] = []
    async for doc in cursor:
        doc = serialize_mongo(doc)
        out.append(MenuItemPublic(**{**doc, "id": doc["_id"], "restaurantId": doc["restaurantId"]}))
    return out


@router.get("/by-tag", response_model=List[MenuItemPublic])
async def list_menu_items_by_tag(
    tag: str,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=200),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    query = {"tags": tag}
    await assert_find_uses_index(db, "menuItems", query, skip=skip, limit=limit)
    cursor = db["menuItems"].find(query).skip(skip).limit(limit)
    out: list[MenuItemPublic] = []
    async for doc in cursor:
        doc = serialize_mongo(doc)
        out.append(MenuItemPublic(**{**doc, "id": doc["_id"], "restaurantId": doc["restaurantId"]}))
    return out


@router.get("/{item_id}", response_model=MenuItemPublic)
async def get_menu_item(item_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    doc = await db["menuItems"].find_one({"_id": to_object_id(item_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Menu item not found")
    doc = serialize_mongo(doc)
    return MenuItemPublic(**{**doc, "id": doc["_id"], "restaurantId": doc["restaurantId"]})


@router.patch("/{item_id}")
async def update_menu_item(item_id: str, patch: dict, db: AsyncIOMotorDatabase = Depends(get_db)):
    if "restaurantId" in patch:
        patch["restaurantId"] = to_object_id(patch["restaurantId"])
    result = await db["menuItems"].update_one({"_id": to_object_id(item_id)}, {"$set": patch})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return {"matched": result.matched_count, "modified": result.modified_count}


@router.patch("/bulk/update-many")
async def update_menu_items_many(req: UpdateManyRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    filt = dict(req.filter)
    if "restaurantId" in filt and isinstance(filt["restaurantId"], str):
        filt["restaurantId"] = to_object_id(filt["restaurantId"])
    result = await db["menuItems"].update_many(filt, req.update)
    return {"matched": result.matched_count, "modified": result.modified_count}


@router.post("/{item_id}/tags:add")
async def add_tags(
    item_id: str,
    tags: List[str],
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    result = await db["menuItems"].update_one(
        {"_id": to_object_id(item_id)},
        {"$addToSet": {"tags": {"$each": tags}}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return {"matched": result.matched_count, "modified": result.modified_count}


@router.post("/{item_id}/tags:remove")
async def remove_tags(
    item_id: str,
    tags: List[str],
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    result = await db["menuItems"].update_one(
        {"_id": to_object_id(item_id)},
        {"$pull": {"tags": {"$in": tags}}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return {"matched": result.matched_count, "modified": result.modified_count}


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_menu_item(item_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    await db["menuItems"].delete_one({"_id": to_object_id(item_id)})
    return None


@router.post("/bulk/delete-many")
async def delete_menu_items_many(req: DeleteManyRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    filt = dict(req.filter)
    if "restaurantId" in filt and isinstance(filt["restaurantId"], str):
        filt["restaurantId"] = to_object_id(filt["restaurantId"])
    result = await db["menuItems"].delete_many(filt)
    return {"deleted": result.deleted_count}

