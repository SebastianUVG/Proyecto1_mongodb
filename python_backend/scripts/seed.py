import argparse
import os
import random
from datetime import datetime, timedelta

from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient


def main() -> None:
    load_dotenv()
    uri = os.getenv("MONGO_URI")
    if not uri:
        raise RuntimeError("MONGO_URI is required")

    parser = argparse.ArgumentParser()
    parser.add_argument("--restaurants", type=int, default=30)
    parser.add_argument("--users", type=int, default=200)
    parser.add_argument("--menu-items", type=int, default=300)
    parser.add_argument("--orders", type=int, default=50_000)
    parser.add_argument("--reviews", type=int, default=5_000)
    args = parser.parse_args()

    client = MongoClient(uri)
    db = client["restaurant_system"]

    # Clean (optional but useful in dev)
    db.restaurants.delete_many({})
    db.users.delete_many({})
    db.menuItems.delete_many({})
    db.orders.delete_many({})
    db.reviews.delete_many({})

    # Restaurants
    categories = ["Italian", "Mexican", "Fast Food", "Seafood", "Dessert", "Coffee"]
    restaurants = []
    for i in range(args.restaurants):
        lng = -90.55 + random.random() * 0.1
        lat = 14.55 + random.random() * 0.15
        restaurants.append(
            {
                "_id": ObjectId(),
                "name": f"Restaurant {i}",
                "description": f"Description for restaurant {i}",
                "category": random.choice(categories),
                "location": {"type": "Point", "coordinates": [lng, lat]},
                "ratingAverage": 0.0,
                "createdAt": datetime.utcnow(),
            }
        )
    db.restaurants.insert_many(restaurants)

    # Users
    users = []
    for i in range(args.users):
        users.append(
            {
                "_id": ObjectId(),
                "name": f"User {i}",
                "email": f"user{i}@example.com",
                "password": "hashed_password",
                "role": "customer" if i % 20 else "admin",
                "createdAt": datetime.utcnow(),
            }
        )
    db.users.insert_many(users, ordered=False)

    # Menu items
    tags_pool = ["pizza", "italian", "cheese", "spicy", "vegan", "gluten-free", "coffee", "dessert"]
    menu_items = []
    for i in range(args.menu_items):
        r = random.choice(restaurants)
        menu_items.append(
            {
                "_id": ObjectId(),
                "restaurantId": r["_id"],
                "name": f"Item {i}",
                "price": random.choice([25, 35, 45, 60, 80, 100]),
                "category": random.choice(["Main Dish", "Side", "Drink", "Dessert"]),
                "tags": random.sample(tags_pool, k=random.randint(1, 3)),
            }
        )
    db.menuItems.insert_many(menu_items)

    # Index menu items by restaurant for coherent orders
    items_by_restaurant: dict[ObjectId, list[dict]] = {}
    for it in menu_items:
        items_by_restaurant.setdefault(it["restaurantId"], []).append(it)

    # Orders (>= 50,000 docs by default)
    statuses = ["pending", "completed", "cancelled"]
    orders = []
    start_time = datetime.utcnow() - timedelta(days=60)
    for i in range(args.orders):
        r = random.choice(restaurants)
        u = random.choice(users)
        candidate_items = items_by_restaurant.get(r["_id"], [])
        if not candidate_items:
            candidate_items = menu_items

        k = random.randint(1, 5)
        chosen = random.sample(candidate_items, k=min(k, len(candidate_items)))
        items = []
        total = 0.0
        for ci in chosen:
            qty = random.randint(1, 3)
            price = float(ci["price"])
            items.append(
                {
                    "menuItemId": ci["_id"],
                    "name": ci["name"],
                    "quantity": qty,
                    "price": price,
                }
            )
            total += price * qty

        created_at = start_time + timedelta(minutes=random.randint(0, 60 * 24 * 60))
        orders.append(
            {
                "_id": ObjectId(),
                "userId": u["_id"],
                "restaurantId": r["_id"],
                "items": items,
                "status": random.choice(statuses),
                "totalAmount": float(total),
                "createdAt": created_at,
            }
        )

        if len(orders) >= 2000:
            db.orders.insert_many(orders)
            orders.clear()

    if orders:
        db.orders.insert_many(orders)

    # Reviews (some tied to orders, some not)
    order_ids = list(db.orders.find({}, {"_id": 1}).limit(min(args.reviews, 20_000)))
    order_ids = [o["_id"] for o in order_ids]
    reviews = []
    for i in range(args.reviews):
        r = random.choice(restaurants)
        u = random.choice(users)
        order_id = random.choice(order_ids) if (order_ids and random.random() < 0.7) else None
        reviews.append(
            {
                "_id": ObjectId(),
                "restaurantId": r["_id"],
                "userId": u["_id"],
                "orderId": order_id,
                "rating": random.randint(1, 5),
                "comment": f"Review {i}",
                "createdAt": datetime.utcnow(),
            }
        )
        if len(reviews) >= 2000:
            db.reviews.insert_many(reviews)
            reviews.clear()
    if reviews:
        db.reviews.insert_many(reviews)

    print("Seed complete.")
    print(f"restaurants: {db.restaurants.count_documents({})}")
    print(f"users: {db.users.count_documents({})}")
    print(f"menuItems: {db.menuItems.count_documents({})}")
    print(f"orders: {db.orders.count_documents({})}")
    print(f"reviews: {db.reviews.count_documents({})}")


if __name__ == "__main__":
    main()

