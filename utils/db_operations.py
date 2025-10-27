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
            # Отсоединяем объект от сессии, чтобы избежать нежелательных побочных эффектов вроде повторных запросов
            session.expunge(new_product)
            logger.info(
                f"✅ Создан новый продукт ID={new_product.id}: {new_product.name}"
            )
            return new_product
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Ошибка создания продукта: {e}", exc_info=True)
            raise


def product_delete_by_id(session_local: sessionmaker, product_id: int) -> int:
    """
    Удаляет продукт по ID.
    :param session_local: Фабрика сессий SQLAlchemy.
    :param product_id: ID продукта для удаления.
    :return: int: Id удаленного продукта
    """
    # Открываем сессию
    with session_local() as session:
        # Пытаемся найти продукт по ID
        product = session.get(Product, product_id)
        if not product:
            logger.warning(f"❌ Продукт с ID={product_id} не найден для удаления.")
            return -1

        session.delete(product)
        session.commit()
        logger.info(f"✅ Продукт с ID={product_id} успешно удален.")
        return product_id


def product_update_by_id(
    session_local: sessionmaker, product_id: int, **kwargs
) -> Product | None:
    """
    Обновляет продукт по ID с переданными полями.
    :param product_id: ID продукта для обновления.
    :param kwargs: Поля для обновления с их новыми значениями.
    :return: Обновленный объект продукта или None, если продукт не найден.

    """
    with session_local() as session:
        product = session.get(Product, product_id)
        # Проверка существования продукта
        if not product:
            logger.warning(f"❌ Продукт с ID={product_id} не найден для обновления.")
            return None

        # Обновление полей продукта
        try:
            for key, value in kwargs.items():
                if hasattr(product, key):
                    setattr(product, key, value)
            session.commit()

        except Exception as e:
            session.rollback()
            logger.error(
                f"❌ Ошибка обновления продукта ID={product_id}: {e}", exc_info=True
            )
            raise

        session.expunge(product)
        logger.info(f"✅ Продукт с ID={product_id} успешно обновлен.")
        return product


def product_get_by_id(session_local: sessionmaker, product_id: int) -> Product | None:
    """
    Получает продукт по ID.
    :param session_local: Фабрика сессий SQLAlchemy.
    :param product_id: ID продукта для получения.
    :return: Объект продукта или None, если продукт не найден.
    """
    with session_local() as session:
        product = session.get(Product, product_id)
        if not product:
            logger.warning(f"❌ Продукт с ID={product_id} не найден.")
            return None

        session.expunge(product)
        logger.info(f"✅ Продукт с ID={product_id} успешно получен.")
        return product


def product_get_all(session_local: sessionmaker) -> list[Product]:
    """
    Получает все продукты из базы данных.
    :param session_local: Фабрика сессий SQLAlchemy.
    :return: Список всех объектов продуктов.
    """
    with session_local() as session:
        # session.query - создает запрос к базе данных для получения всех продуктов
        # Поддерживает различные методы фильтрации, сортировки и агрегации данных
        products = session.query(Product).all()
        for product in products:
            session.expunge(product)
        logger.info(f"✅ Получено {len(products)} продуктов из базы данных.")
        return products
