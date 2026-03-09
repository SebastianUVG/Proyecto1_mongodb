from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class Location(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: List[float] = Field(
        ...,
        min_items=2,
        max_items=2,
        description="[lng, lat]",
    )


class RestaurantBase(BaseModel):
    name: str
    description: str
    category: str
    location: Location


class RestaurantCreate(RestaurantBase):
    pass


class RestaurantInDB(RestaurantBase):
    id: str = Field(alias="_id")
    ratingAverage: float
    createdAt: datetime


class RestaurantPublic(BaseModel):
    id: str
    name: str
    description: str
    category: str
    location: Location
    ratingAverage: float
    createdAt: datetime


class MenuItemBase(BaseModel):
    restaurantId: str
    name: str
    price: float
    category: str
    tags: List[str] = []


class MenuItemCreate(MenuItemBase):
    pass


class MenuItemInDB(MenuItemBase):
    id: str = Field(alias="_id")


class MenuItemPublic(BaseModel):
    id: str
    restaurantId: str
    name: str
    price: float
    category: str
    tags: List[str]


class UserBase(BaseModel):
    name: str
    email: str
    role: Literal["customer", "admin"] = "customer"


class UserCreate(UserBase):
    password: str


class UserInDB(UserBase):
    id: str = Field(alias="_id")
    password: str
    createdAt: datetime


class UserPublic(BaseModel):
    id: str
    name: str
    email: str
    role: Literal["customer", "admin"]
    createdAt: datetime


class OrderItem(BaseModel):
    menuItemId: str
    name: str
    quantity: int
    price: float


class OrderBase(BaseModel):
    userId: str
    restaurantId: str
    items: List[OrderItem]
    status: Literal["pending", "completed", "cancelled"] = "pending"
    totalAmount: float


class OrderCreate(OrderBase):
    pass


class OrderInDB(OrderBase):
    id: str = Field(alias="_id")
    createdAt: datetime


class OrderPublic(BaseModel):
    id: str
    userId: str
    restaurantId: str
    items: List[OrderItem]
    status: Literal["pending", "completed", "cancelled"]
    totalAmount: float
    createdAt: datetime


class ReviewBase(BaseModel):
    restaurantId: str
    userId: str
    orderId: str
    rating: float
    comment: str


class ReviewCreate(BaseModel):
    rating: float
    comment: str


class ReviewInDB(ReviewBase):
    id: str = Field(alias="_id")
    createdAt: datetime


class ReviewPublic(BaseModel):
    id: str
    restaurantId: str
    userId: str
    orderId: str
    rating: float
    comment: str
    createdAt: datetime


class TopRatedRestaurant(BaseModel):
    restaurantId: str = Field(alias="_id")
    avgRating: float
    totalReviews: int
    restaurant: Optional[list] = None

