# models/models.py
from email.mime import image
from models.base import Base
from sqlalchemy import String, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column


class Product(Base):
    """
    Базовый вариант модели товара.
    """

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    image_url: Mapped[str] = mapped_column(String(255), nullable=True)
    price_shmeckles: Mapped[float] = mapped_column(Float, nullable=False)
    price_flurbos: Mapped[float] = mapped_column(Float, nullable=False)

    def __repr__(self) -> str:
        return f"<Product id={self.id} name={self.name}>"
