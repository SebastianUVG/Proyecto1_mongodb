from fastapi import FastAPI

from .database import create_indexes
from .routers.analytics import router as analytics_router
from .routers.files import router as files_router
from .routers.menu_items import router as menu_items_router
from .routers.orders import router as orders_router
from .routers.restaurants import router as restaurants_router
from .routers.reviews import router as reviews_router
from .routers.users import router as users_router


app = FastAPI(title="Restaurant System API - Python/FastAPI")


@app.on_event("startup")
async def on_startup() -> None:
    await create_indexes()


app.include_router(restaurants_router)
app.include_router(users_router)
app.include_router(menu_items_router)
app.include_router(orders_router)
app.include_router(reviews_router)
app.include_router(files_router)
app.include_router(analytics_router)

