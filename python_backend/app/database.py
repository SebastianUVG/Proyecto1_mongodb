import os
from typing import AsyncGenerator

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise RuntimeError("MONGO_URI environment variable is not set")


client = AsyncIOMotorClient(MONGO_URI)
db: AsyncIOMotorDatabase = client["restaurant_system"]


async def get_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    yield db


async def create_indexes() -> None:
    """Replica de los índices definidos en el backend de Node."""
    # 1️⃣ Simple Index
    await db["users"].create_index("email", unique=True)

    # 2️⃣ Compound Index
    await db["orders"].create_index([("restaurantId", 1), ("createdAt", -1)])

    # 3️⃣ Multikey Index
    await db["menuItems"].create_index("tags")

    # 4️⃣ Geospatial Index
    await db["restaurants"].create_index([("location", "2dsphere")])

    # 5️⃣ Text Index
    await db["restaurants"].create_index(
        [("name", "text"), ("description", "text")]
    )

    # Intento de configurar la BD para rechazar COLLSCAN (si el cluster lo permite).
    # En Atlas compartido puede fallar por permisos; en ese caso se ignora.
    try:
        await client.admin.command({"setParameter": 1, "notablescan": 1})
    except Exception:
        pass

