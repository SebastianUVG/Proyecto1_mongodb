import os
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

import httpx


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")


def _print_title(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def _prompt(msg: str, default: Optional[str] = None) -> str:
    if default is None:
        return input(f"{msg}: ").strip()
    v = input(f"{msg} [{default}]: ").strip()
    return v or default


def _post(client: httpx.Client, path: str, json: Any = None, files: Any = None) -> Any:
    r = client.post(f"{API_BASE_URL}{path}", json=json, files=files, timeout=60)
    r.raise_for_status()
    return r.json() if r.content else None


def _patch(client: httpx.Client, path: str, json: Any = None) -> Any:
    r = client.patch(f"{API_BASE_URL}{path}", json=json, timeout=60)
    r.raise_for_status()
    return r.json() if r.content else None


def _delete(client: httpx.Client, path: str, json: Any = None) -> Any:
    r = client.request("DELETE", f"{API_BASE_URL}{path}", json=json, timeout=60)
    r.raise_for_status()
    return r.json() if r.content else None


def _get(client: httpx.Client, path: str, params: Dict[str, Any] | None = None) -> Any:
    r = client.get(f"{API_BASE_URL}{path}", params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def _run_seed() -> None:
    _print_title("Seed DB (>=50k orders por default)")
    root = Path(__file__).resolve().parents[1]
    script = root / "scripts" / "seed.py"
    print(f"Running: python3 {script}")
    subprocess.check_call(["python3", str(script)])


def _run_explain_report() -> None:
    _print_title("Explain report (executionStats)")
    root = Path(__file__).resolve().parents[1]
    script = root / "scripts" / "explain_report.py"
    print(f"Running: python3 {script}")
    subprocess.check_call(["python3", str(script)])


def main() -> None:
    _print_title("Restaurant System CLI (MongoDB + FastAPI)")
    print(f"API_BASE_URL = {API_BASE_URL}")
    print("Asegúrate de correr el API con uvicorn primero.\n")

    with httpx.Client() as client:
        while True:
            print(
                "\nMenú\n"
                "1) Seed DB (50k+) [script]\n"
                "2) Crear restaurant\n"
                "3) Buscar restaurant (text)\n"
                "4) Restaurants near (geo)\n"
                "5) Crear user\n"
                "6) Obtener user por email (index)\n"
                "7) Crear menu item\n"
                "8) Menu items por tag (index)\n"
                "9) Crear order + review (transacción)\n"
                "10) Orders enriched (lookup + paginación)\n"
                "11) Analytics (top/menu/revenue/counts)\n"
                "12) Upload archivo (GridFS)\n"
                "13) Download archivo (GridFS)\n"
                "14) Explain report [script]\n"
                "15) Update order status (update one)\n"
                "16) Bulk update menu item prices (update many)\n"
                "17) Bulk delete orders by status (delete many)\n"
                "0) Salir\n"
            )
            choice = _prompt("Opción")

            try:
                if choice == "0":
                    return

                if choice == "1":
                    _run_seed()
                    continue

                if choice == "2":
                    name = _prompt("name", "Pizza Place")
                    description = _prompt("description", "Best pizza in town")
                    category = _prompt("category", "Italian")
                    lng = float(_prompt("lng", "-90.5069"))
                    lat = float(_prompt("lat", "14.6349"))
                    res = _post(
                        client,
                        "/restaurants",
                        json={
                            "name": name,
                            "description": description,
                            "category": category,
                            "location": {"type": "Point", "coordinates": [lng, lat]},
                        },
                    )
                    print(res)
                    continue

                if choice == "3":
                    q = _prompt("q", "pizza")
                    res = _get(client, "/restaurants/search", params={"q": q})
                    print(res[:5] if isinstance(res, list) else res)
                    continue

                if choice == "4":
                    lng = float(_prompt("lng", "-90.50"))
                    lat = float(_prompt("lat", "14.63"))
                    max_d = int(_prompt("maxDistance (meters)", "5000"))
                    res = _get(client, "/restaurants/near", params={"lng": lng, "lat": lat, "maxDistance": max_d})
                    print(res[:5] if isinstance(res, list) else res)
                    continue

                if choice == "5":
                    name = _prompt("name", "Juan Pérez")
                    email = _prompt("email", "juan@email.com")
                    password = _prompt("password", "hashed_password")
                    role = _prompt("role (customer/admin)", "customer")
                    res = _post(client, "/users", json={"name": name, "email": email, "password": password, "role": role})
                    print(res)
                    continue

                if choice == "6":
                    email = _prompt("email", "juan@email.com")
                    res = _get(client, "/users/by-email", params={"email": email})
                    print(res)
                    continue

                if choice == "7":
                    restaurant_id = _prompt("restaurantId")
                    name = _prompt("name", "Pizza Pepperoni")
                    price = float(_prompt("price", "80"))
                    category = _prompt("category", "Main Dish")
                    tags = _prompt("tags (comma-separated)", "pizza,italian,cheese")
                    res = _post(
                        client,
                        "/menu-items",
                        json={
                            "restaurantId": restaurant_id,
                            "name": name,
                            "price": price,
                            "category": category,
                            "tags": [t.strip() for t in tags.split(",") if t.strip()],
                        },
                    )
                    print(res)
                    continue

                if choice == "8":
                    tag = _prompt("tag", "pizza")
                    res = _get(client, "/menu-items/by-tag", params={"tag": tag})
                    print(res[:5] if isinstance(res, list) else res)
                    continue

                if choice == "9":
                    user_id = _prompt("userId")
                    restaurant_id = _prompt("restaurantId")
                    item_menu_id = _prompt("menuItemId")
                    item_name = _prompt("item name", "Pizza Pepperoni")
                    qty = int(_prompt("quantity", "2"))
                    price = float(_prompt("price", "80"))
                    rating = float(_prompt("review rating (1-5)", "5"))
                    comment = _prompt("review comment", "Excelente servicio")
                    res = _post(
                        client,
                        "/orders/with-review",
                        json={
                            "order": {
                                "userId": user_id,
                                "restaurantId": restaurant_id,
                                "items": [
                                    {
                                        "menuItemId": item_menu_id,
                                        "name": item_name,
                                        "quantity": qty,
                                        "price": price,
                                    }
                                ],
                                "status": "completed",
                            },
                            "review": {"rating": rating, "comment": comment},
                        },
                    )
                    print(res)
                    continue

                if choice == "10":
                    restaurant_id = _prompt("restaurantId (optional)", "")
                    params: dict[str, Any] = {"skip": 0, "limit": 10, "lite": True}
                    if restaurant_id:
                        params["restaurantId"] = restaurant_id
                    res = _get(client, "/orders/enriched/query", params=params)
                    print(res[:3] if isinstance(res, list) else res)
                    continue

                if choice == "11":
                    counts = _get(client, "/analytics/counts")
                    top_r = _get(client, "/analytics/top-restaurants")
                    top_i = _get(client, "/analytics/top-menu-items")
                    rev = _get(client, "/analytics/revenue-by-restaurant")
                    print("counts:", counts)
                    print("top-restaurants:", top_r[:3] if isinstance(top_r, list) else top_r)
                    print("top-menu-items:", top_i[:3] if isinstance(top_i, list) else top_i)
                    print("revenue-by-restaurant:", rev[:3] if isinstance(rev, list) else rev)
                    continue

                if choice == "12":
                    path = Path(_prompt("path to file"))
                    if not path.exists():
                        print("File not found.")
                        continue
                    with path.open("rb") as f:
                        res = _post(
                            client,
                            "/files/upload",
                            files={"file": (path.name, f, "application/octet-stream")},
                        )
                    print(res)
                    continue

                if choice == "13":
                    gridfs_id = _prompt("gridfs_id")
                    out_path = Path(_prompt("output path", f"./download_{gridfs_id}.bin"))
                    r = client.get(f"{API_BASE_URL}/files/{gridfs_id}", timeout=60)
                    if r.status_code != 200:
                        print(r.status_code, r.text)
                        continue
                    out_path.write_bytes(r.content)
                    print(f"Saved to {out_path.resolve()}")
                    continue

                if choice == "14":
                    _run_explain_report()
                    continue

                if choice == "15":
                    order_id = _prompt("orderId")
                    new_status = _prompt("status (pending/completed/cancelled)", "completed")
                    res = _patch(client, f"/orders/{order_id}", json={"status": new_status})
                    print(res)
                    continue

                if choice == "16":
                    restaurant_id = _prompt("restaurantId")
                    new_price = float(_prompt("new price", "90"))
                    res = _patch(
                        client,
                        "/menu-items/bulk/update-many",
                        json={
                            "filter": {"restaurantId": restaurant_id},
                            "update": {"$set": {"price": new_price}},
                        },
                    )
                    print(res)
                    continue

                if choice == "17":
                    status_ = _prompt("status to delete", "cancelled")
                    res = _post(
                        client,
                        "/orders/bulk/delete-many",
                        json={"filter": {"status": status_}},
                    )
                    print(res)
                    continue

                print("Opción inválida.")
            except httpx.HTTPStatusError as e:
                print("HTTP error:", e.response.status_code, e.response.text)
            except Exception as e:
                print("Error:", e)


if __name__ == "__main__":
    main()

