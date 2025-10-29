"""
Простые Pydantic схемы для Product
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional


class ProductCreate(BaseModel):
    """Данные для создания продукта"""

    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    price_shmeckles: float
    price_flurbos: float


class Product(BaseModel):
    """Данные продукта из БД"""

    id: int
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    price_shmeckles: float
    price_flurbos: float

    model_config = ConfigDict(from_attributes=True)  # Позволяет создавать из ORM
