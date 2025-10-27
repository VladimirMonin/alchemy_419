# utils/db_initial.py
from sqlalchemy import create_engine
from models.base import Base
from models.models import Product
import os
from settings import DB_NAME


def init_db():
    """
    Функция инициализации базы данных.
    """
    if not os.path.exists(DB_NAME):

        # Создаем движок базы данных
        engine = create_engine(f"sqlite:///{DB_NAME}", echo=True)

        # Создаем все таблицы, определенные в моделях
        Base.metadata.create_all(engine)
        print("База данных инициализирована.")

    else:
        print("База данных уже существует.")
