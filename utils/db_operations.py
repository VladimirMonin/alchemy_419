# utils/db_operations.py
# Модуль для CRUD операций с базой данных используя SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.models import Product
from settings import DB_NAME
import logging

# Создаём именованный логгер для этого модуля
logger = logging.getLogger(__name__)


def get_engine(db_name=DB_NAME):
    """Создает и возвращает движок базы данных."""
    engine = create_engine(f"sqlite:///{db_name}", echo=True)
    logger.info(f"Создан движок базы данных для {db_name}")
    return engine


def get_session_factory(engine):
    """Создает и возвращает фабрику сессий.
    :param engine: Движок базы данных SQLAlchemy.
    :return: Фабрика сессий SQLAlchemy.

    bind - Движок базы данных, к которому будет привязана сессия.

    autocommit - Если установлено в False, изменения не будут автоматически
    зафиксированы в базе данных. Это позволяет явно контролировать транзакции.

    autoflush - Если установлено в False, изменения не будут автоматически
    отправлены в базу данных перед выполнением запросов. Это может быть полезно
    в ситуациях, когда необходимо выполнить несколько операций с базой данных
    в рамках одной транзакции.

    expire_on_commit - Если установлено в False, объекты в сессии не будут
    удалены из сессии после фиксации транзакции. Это позволяет повторно использовать объекты
    после коммита без необходимости повторного запроса к базе данных.
    """
    logger.info("Создана фабрика сессий для базы данных.")
    return sessionmaker(
        bind=engine, autocommit=False, autoflush=False, expire_on_commit=False
    )


def product_create(
    session_local: sessionmaker,
    name: str,
    description: str | None,
    image_url: str | None,
    price_shmeckles: float,
    price_flurbos: float,
) -> Product:
    """Создает новый продукт в базе данных.
    :param session_local: Фабрика сессий SQLAlchemy.
    :param name: Название продукта.
    :param description: Описание продукта.
    :param image_url: URL изображения продукта.
    :param price_shmeckles: Цена продукта в шмекелях.
    :param price_flurbos: Цена продукта во флубрах.
    :return: Созданный объект продукта.
    """
    with session_local() as session:
        try:
            new_product = Product(
                name=name,
                description=description,
                image_url=image_url,
                price_shmeckles=price_shmeckles,
                price_flurbos=price_flurbos,
            )
            session.add(new_product)
            session.commit()
            logger.info(
                f"✅ Создан новый продукт ID={new_product.id}: {new_product.name}"
            )
            return new_product
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Ошибка создания продукта: {e}", exc_info=True)
            raise
