# utils/db_operations.py
# Модуль для CRUD операций с базой данных используя SQLAlchemy
from sqlalchemy import create_engine, select, or_
from sqlalchemy.orm import sessionmaker, selectinload
from models.models import Product as ProductORM, Category as CategoryORM, Tag as TagORM
from config import settings
from schemas.schemas import (
    ProductCreate,
    Product,
    CategoryCreate,
    Category,
    TagCreate,
    Tag,
)
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


# ============================================
# CRUD для Category
# ============================================


def category_create(
    session_local: sessionmaker, category_data: CategoryCreate
) -> Category:
    """
    Создание новой категории

    :param session_local: Фабрика сессий SQLAlchemy.
    :param category_data: Данные для создания категории
    :return: Category с id и name категории
    """
    with session_local() as session:
        try:
            # Проверка на уникальность имени
            existing = session.execute(
                select(CategoryORM).where(CategoryORM.name == category_data.name)
            ).scalar_one_or_none()

            if existing:
                logger.warning(f"⚠️ Категория '{category_data.name}' уже существует")
                return Category.model_validate(existing)

            # Создаём новую категорию
            new_category = CategoryORM(name=category_data.name)

            session.add(new_category)
            session.commit()
            session.refresh(new_category)

            result = Category.model_validate(new_category)
            logger.info(f"✅ Категория создана: ID={result.id}, Name={result.name}")
            return result

        except Exception as e:
            session.rollback()
            logger.error(f"❌ Ошибка создания категории: {e}", exc_info=True)
            raise


def category_get_by_id(
    session_local: sessionmaker, category_id: int
) -> Category | None:
    """Получить категорию по ID"""
    with session_local() as session:
        category = session.get(CategoryORM, category_id)
        if not category:
            logger.warning(f"❌ Категория с ID={category_id} не найдена.")
            return None

        result = Category.model_validate(category)
        logger.info(f"✅ Категория с ID={category_id} успешно получена.")
        return result


def category_get_all(session_local: sessionmaker) -> list[Category]:
    """Получить все категории"""
    with session_local() as session:
        stmt = select(CategoryORM)
        categories = session.scalars(stmt).all()

        result = [Category.model_validate(cat) for cat in categories]
        logger.info(f"✅ Получено {len(result)} категорий из базы данных.")
        return result


# ============================================
# CRUD для Tag
# ============================================


def tag_create(session_local: sessionmaker, tag_data: TagCreate) -> Tag:
    """
    Создание нового тега

    :param session_local: Фабрика сессий SQLAlchemy.
    :param tag_data: Данные для создания тега
    :return: Tag с id и name тега
    """
    with session_local() as session:
        try:
            # Проверка на уникальность имени
            existing = session.execute(
                select(TagORM).where(TagORM.name == tag_data.name)
            ).scalar_one_or_none()

            if existing:
                logger.warning(f"⚠️ Тег '{tag_data.name}' уже существует")
                return Tag.model_validate(existing)

            # Создаём новый тег
            new_tag = TagORM(name=tag_data.name)

            session.add(new_tag)
            session.commit()
            session.refresh(new_tag)

            result = Tag.model_validate(new_tag)
            logger.info(f"✅ Тег создан: ID={result.id}, Name={result.name}")
            return result

        except Exception as e:
            session.rollback()
            logger.error(f"❌ Ошибка создания тега: {e}", exc_info=True)
            raise


def tag_get_by_id(session_local: sessionmaker, tag_id: int) -> Tag | None:
    """Получить тег по ID"""
    with session_local() as session:
        tag = session.get(TagORM, tag_id)
        if not tag:
            logger.warning(f"❌ Тег с ID={tag_id} не найден.")
            return None

        result = Tag.model_validate(tag)
        logger.info(f"✅ Тег с ID={tag_id} успешно получен.")
        return result


def tag_get_all(session_local: sessionmaker) -> list[Tag]:
    """Получить все теги"""
    with session_local() as session:
        stmt = select(TagORM)
        tags = session.scalars(stmt).all()

        result = [Tag.model_validate(tag) for tag in tags]
        logger.info(f"✅ Получено {len(result)} тегов из базы данных.")
        return result


# ============================================
# Обновленные функции для Product с поддержкой связей
# ============================================


def product_create_with_relations(
    session_local: sessionmaker,
    product_data: ProductCreate,
    strict_validation: bool = True,
) -> Product:
    """
    Создание нового продукта со связями (категория и теги)

    :param session_local: Фабрика сессий SQLAlchemy.
    :param product_data: Данные продукта (ProductCreate) с category_id и tag_ids
    :param strict_validation: Если True, выбрасывает исключение при отсутствии категории/тегов
    :return: Product с данными созданного продукта
    """
    with session_local() as session:
        try:
            # 1. Создаём базовый продукт через распаковку DTO
            #    Исключаем служебные поля для связей
            product_dict = product_data.model_dump(exclude={"category_id", "tag_ids"})
            new_product = ProductORM(**product_dict)

            # 2. Обрабатываем категорию (FK связь)
            if product_data.category_id:
                logger.info(f"Привязка категории ID: {product_data.category_id}")

                category_orm = session.get(CategoryORM, product_data.category_id)

                if not category_orm:
                    error_msg = f"Категория с ID {product_data.category_id} не найдена"
                    logger.error(f"❌ {error_msg}")
                    if strict_validation:
                        raise ValueError(error_msg)
                    else:
                        logger.warning(f"⚠️ Продукт будет создан без категории")
                else:
                    # Привязываем через объект (SQLAlchemy автоматически установит category_id)
                    new_product.category = category_orm

            # 3. Обрабатываем теги (M2M связь)
            if product_data.tag_ids:
                logger.info(f"Привязка тегов: {product_data.tag_ids}")

                # Загружаем все теги одним запросом
                tags_stmt = select(TagORM).where(TagORM.id.in_(product_data.tag_ids))
                tags_orm = session.execute(tags_stmt).scalars().all()

                # Проверяем, что все теги найдены
                found_ids = {tag.id for tag in tags_orm}
                missing_ids = set(product_data.tag_ids) - found_ids

                if missing_ids:
                    error_msg = f"Теги с ID {missing_ids} не найдены"
                    logger.error(f"❌ {error_msg}")
                    if strict_validation:
                        raise ValueError(error_msg)
                    else:
                        logger.warning(
                            f"⚠️ Будут привязаны только найденные теги: {found_ids}"
                        )

                # Устанавливаем связь M2M
                new_product.tags = list(tags_orm)

            # 4. Сохраняем продукт
            session.add(new_product)
            session.commit()

            # 5. Перезагружаем с полными связями для возврата
            stmt = (
                select(ProductORM)
                .where(ProductORM.id == new_product.id)
                .options(
                    selectinload(ProductORM.category), selectinload(ProductORM.tags)
                )
            )
            refreshed_product = session.execute(stmt).scalar_one()

            result = Product.model_validate(refreshed_product)

            logger.info(
                f"✅ Продукт создан: ID={result.id}, "
                f"Category={result.category.name if result.category else 'Нет'}, "
                f"Tags={[tag.name for tag in result.tags]}"
            )
            return result

        except Exception as e:
            session.rollback()
            logger.error(f"❌ Ошибка создания продукта: {e}", exc_info=True)
            raise


def product_get_by_id_with_relations(
    session_local: sessionmaker, product_id: int
) -> Product | None:
    """
    Получает продукт по ID с загрузкой категории и тегов

    :param session_local: Фабрика сессий SQLAlchemy.
    :param product_id: ID продукта для получения.
    :return: Product или None, если продукт не найден.
    """
    with session_local() as session:
        stmt = (
            select(ProductORM)
            .where(ProductORM.id == product_id)
            .options(selectinload(ProductORM.category), selectinload(ProductORM.tags))
        )

        product = session.execute(stmt).scalar_one_or_none()

        if not product:
            logger.warning(f"❌ Продукт с ID={product_id} не найден.")
            return None

        result = Product.model_validate(product)
        logger.info(f"✅ Продукт с ID={product_id} успешно получен со связями.")
        return result


def product_get_all_with_relations(
    session_local: sessionmaker, skip: int = 0, limit: int = 100
) -> list[Product]:
    """
    Получить все продукты с категориями и тегами

    :param session_local: Фабрика сессий SQLAlchemy.
    :param skip: Количество записей для пропуска
    :param limit: Максимальное количество записей
    :return: Список всех Product со связями.
    """
    with session_local() as session:
        stmt = (
            select(ProductORM)
            .options(selectinload(ProductORM.category), selectinload(ProductORM.tags))
            .offset(skip)
            .limit(limit)
        )

        products = session.execute(stmt).scalars().all()

        result = [Product.model_validate(p) for p in products]
        logger.info(f"✅ Получено {len(result)} продуктов со связями из базы данных.")
        return result


def product_search_advanced(session_local: sessionmaker, search: str) -> list[Product]:
    """
    Расширенный поиск продуктов по названию, категории или тегам

    :param session_local: Фабрика сессий SQLAlchemy.
    :param search: Поисковый запрос
    :return: Список найденных продуктов со связями
    """
    with session_local() as session:
        logger.info(f"🔍 Расширенный поиск: '{search}'")

        pattern = f"%{search}%"

        stmt = (
            select(ProductORM)
            .outerjoin(ProductORM.category)
            .outerjoin(ProductORM.tags)
            .where(
                or_(
                    ProductORM.name.ilike(pattern),
                    CategoryORM.name.ilike(pattern),
                    TagORM.name.ilike(pattern),
                )
            )
            .options(selectinload(ProductORM.category), selectinload(ProductORM.tags))
            .distinct()
        )

        products = session.execute(stmt).scalars().unique().all()

        result = [Product.model_validate(p) for p in products]
        logger.info(f"✅ Найдено продуктов: {len(result)}")
        return result
