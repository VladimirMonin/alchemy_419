# utils/db_operations.py
# Модуль для CRUD операций с базой данных используя SQLAlchemy
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from models.models import Product as ProductORM
from config import settings
from schemas.schemas import ProductCreate, Product
import logging

# Создаём именованный логгер для этого модуля
logger = logging.getLogger(__name__)


def get_engine(db_name=None):
    """Создает и возвращает движок базы данных."""
    db = db_name or settings.db_name
    engine = create_engine(f"sqlite:///{db}", echo=settings.db_echo)
    logger.info(f"Создан движок базы данных для {db}")
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
    product_data: ProductCreate,
) -> Product:
    """
    Создает новый продукт используя Pydantic схему.

    :param session_local: Фабрика сессий SQLAlchemy.
    :param product_data: Данные продукта (ProductCreate)
    :return: ProductRead с данными созданного продукта
    """
    with session_local() as session:
        try:
            # Создаем ORM объект из Pydantic модели
            new_product = ProductORM(**product_data.model_dump())
            session.add(new_product)
            session.commit()
            session.refresh(new_product)

            # Преобразуем ORM в Pydantic
            result = Product.model_validate(new_product)

            logger.info(f"✅ Создан новый продукт ID={result.id}: {result.name}")
            return result

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
        product = session.get(ProductORM, product_id)
        if not product:
            logger.warning(f"❌ Продукт с ID={product_id} не найден для удаления.")
            return -1

        session.delete(product)
        session.commit()
        logger.info(f"✅ Продукт с ID={product_id} успешно удален.")
        return product_id


def product_update(session_local: sessionmaker, product_data: Product) -> Product:
    """
    Обновляет продукт используя полную Pydantic модель Product.

    :param session_local: Фабрика сессий SQLAlchemy.
    :param product_data: Полные данные продукта (Product) включая ID
    :return: Product с обновленными данными
    """
    with session_local() as session:
        product = session.get(ProductORM, product_data.id)

        if not product:
            logger.warning(
                f"❌ Продукт с ID={product_data.id} не найден для обновления."
            )
            raise ValueError(f"Продукт с ID={product_data.id} не найден")

        try:
            # Обновляем все поля из Pydantic модели
            update_data = product_data.model_dump()

            for key, value in update_data.items():
                setattr(product, key, value)

            session.commit()
            session.refresh(product)

            result = Product.model_validate(product)
            logger.info(f"✅ Продукт с ID={product_data.id} успешно обновлен.")
            return result

        except Exception as e:
            session.rollback()
            logger.error(
                f"❌ Ошибка обновления продукта ID={product_data.id}: {e}",
                exc_info=True,
            )
            raise


def product_get_by_id(session_local: sessionmaker, product_id: int) -> Product | None:
    """
    Получает продукт по ID, возвращает ProductRead.
    :param session_local: Фабрика сессий SQLAlchemy.
    :param product_id: ID продукта для получения.
    :return: ProductRead или None, если продукт не найден.
    """
    with session_local() as session:
        product = session.get(ProductORM, product_id)
        if not product:
            logger.warning(f"❌ Продукт с ID={product_id} не найден.")
            return None

        result = Product.model_validate(product)
        logger.info(f"✅ Продукт с ID={product_id} успешно получен.")
        return result


def product_get_all(session_local: sessionmaker) -> list[Product]:
    """
    Получает все продукты, возвращает список ProductRead.
    :param session_local: Фабрика сессий SQLAlchemy.
    :return: Список всех ProductRead.
    """
    with session_local() as session:
        # Создаем statement (инструкцию) для запроса всех продуктов
        stmt = select(ProductORM)
        # Выполняем запрос и получаем все объекты Product
        products = session.scalars(stmt).all()

        result = [Product.model_validate(p) for p in products]
        logger.info(f"✅ Получено {len(result)} продуктов из базы данных.")
        return result


def product_like_name(
    session_local: sessionmaker, name_substring: str
) -> list[Product]:
    """
    Получает продукты по подстроке в названии.
    :param session_local: Фабрика сессий SQLAlchemy.
    :param name_substring: Подстрока для поиска в названии продукта.
    :return: Список ProductRead, соответствующих критерию поиска.
    """
    with session_local() as session:
        # Создаем statement (инструкцию) для запроса продуктов по подстроке в названии
        stmt = select(ProductORM).where(ProductORM.name.ilike(f"%{name_substring}%"))
        # Выполняем запрос и получаем все объекты Product
        products = session.scalars(stmt).all()

        result = [Product.model_validate(p) for p in products]
        logger.info(
            f"✅ Найдено {len(result)} продуктов, содержащих '{name_substring}' в названии."
        )
        return result
