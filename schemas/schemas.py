from pydantic import BaseModel, ConfigDict
from typing import Optional, List


class CategoryBase(BaseModel):
    """Базовая схема категории"""
    name: str


class CategoryCreate(CategoryBase):
    """Создание категории"""
    pass


class Category(CategoryBase):
    """Категория из БД"""
    id: int
    
    model_config = ConfigDict(from_attributes=True)


class TagBase(BaseModel):
    """Базовая схема тега"""
    name: str


class TagCreate(TagBase):
    """Создание тега"""
    pass


class Tag(TagBase):
    """Тег из БД"""
    id: int
    
    model_config = ConfigDict(from_attributes=True)


class ProductCreate(BaseModel):
    """Данные для создания продукта"""
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    price_shmeckles: float
    price_flurbos: float
    category_id: Optional[int] = None
    tag_ids: List[int] = []  # Список ID тегов


class Product(BaseModel):
    """Продукт из БД со связями"""
    id: int
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    price_shmeckles: float
    price_flurbos: float
    category: Optional[Category] = None  # Вложенная категория
    tags: List[Tag] = []  # Список тегов

    model_config = ConfigDict(from_attributes=True)