# utils/db_initial.py
from sqlalchemy import create_engine
from models.base import Base
from models.models import Product
import os

DB_NAME = "products.db"


def init_db():
    """
    Функция инициализации базы данных.
    """

    # Создаем движок базы данных
    engine = create_engine(f"sqlite:///{DB_NAME}", echo=True)

    # Создаем все таблицы, определенные в моделях
    Base.metadata.create_all(engine)
    print("База данных инициализирована.")


if __name__ == "__main__":
    # Проверяем существование файла БД
    if not os.path.exists(DB_NAME):
        init_db()
    else:
        print("База данных уже существует.")
