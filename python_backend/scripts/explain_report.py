import json
import os
from datetime import datetime
from pathlib import Path

from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient


def _write(out_dir: Path, name: str, payload: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{name}.json").write_text(
        json.dumps(payload, indent=2, default=str, ensure_ascii=False)
    )

def _explain_find(
    db,
    *,
    collection: str,
    filter_: dict,
    limit: int = 0,
    skip: int = 0,
    sort: dict | None = None,
    projection: dict | None = None,
) -> dict:
    cmd: dict = {
        "explain": {
            "find": collection,
            "filter": filter_,
        },
        "verbosity": "executionStats",
    }
    if limit:
        cmd["explain"]["limit"] = limit
    if skip:
        cmd["explain"]["skip"] = skip
    if sort:
        cmd["explain"]["sort"] = sort
    if projection:
        cmd["explain"]["projection"] = projection
    return db.command(cmd)


def main() -> None:
    load_dotenv()
    uri = os.getenv("MONGO_URI")
    if not uri:
        raise RuntimeError("MONGO_URI is required")

    client = MongoClient(uri)
    db = client["restaurant_system"]

    # Ensure required indexes exist before explaining queries
    db.users.create_index([("email", 1)], unique=True)
    db.orders.create_index([("restaurantId", 1), ("createdAt", -1)])
    db.menuItems.create_index([("tags", 1)])
    db.restaurants.create_index([("location", "2dsphere")])
    db.restaurants.create_index([("name", "text"), ("description", "text")])

    out_dir = Path(__file__).resolve().parents[1] / "docs" / "explain"

    sample_restaurant = db.restaurants.find_one()
    sample_user = db.users.find_one()
    sample_menu_item = db.menuItems.find_one({"tags": {"$exists": True, "$ne": []}})
    if not sample_menu_item:
        sample_menu_item = db.menuItems.find_one()

    # users.email (simple unique index)
    email = (sample_user or {}).get("email", "no-one@example.com")
    _write(
        out_dir,
        "users_find_by_email",
        _explain_find(db, collection="users", filter_={"email": email}, limit=1),
    )

    # menuItems.tags (multikey)
    tag = None
    if sample_menu_item and sample_menu_item.get("tags"):
        tag = sample_menu_item["tags"][0]
    tag = tag or "pizza"
    _write(
        out_dir,
        "menuItems_find_by_tag",
        _explain_find(db, collection="menuItems", filter_={"tags": tag}, limit=20),
    )

    # restaurants text index
    _write(
        out_dir,
        "restaurants_text_search",
        _explain_find(
            db,
            collection="restaurants",
            filter_={"$text": {"$search": "pizza"}},
            limit=20,
        ),
    )

    # restaurants geospatial index (2dsphere)
    _write(
        out_dir,
        "restaurants_near_query",
        _explain_find(
            db,
            collection="restaurants",
            filter_={
                "location": {
                    "$near": {
                        "$geometry": {"type": "Point", "coordinates": [-90.50, 14.63]},
                        "$maxDistance": 5000,
                    }
                }
            },
            limit=20,
        ),
    )

    # orders compound index (restaurantId + createdAt)
    restaurant_id = (sample_restaurant or {}).get("_id") or ObjectId()
    _write(
        out_dir,
        "orders_by_restaurant_sorted",
        _explain_find(
            db,
            collection="orders",
            filter_={"restaurantId": restaurant_id},
            sort={"createdAt": -1},
            skip=0,
            limit=20,
        ),
    )

    # timestamped summary
    _write(
        out_dir,
        "meta",
        {"generatedAt": datetime.utcnow().isoformat() + "Z"},
    )

    print(f"Explain outputs written to: {out_dir}")


if __name__ == "__main__":
    main()

