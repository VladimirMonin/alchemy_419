# utils/db_operations.py
"""
Модуль CRUD операций для работы с базой данных через SQLAlchemy.

Архитектура и принципы:
-----------------------
1. **Управление транзакциями**: Используется декоратор @with_transaction для автоматического
   управления транзакциями (commit при успехе, rollback при ошибках).

2. **Загрузка связей**: Все функции работы с Product используют явную загрузку связей
   через selectinload() для избежания проблем с lazy="raise_on_sql".

3. **Валидация данных**: Строгая проверка существования связанных сущностей (категории, теги)
   перед выполнением операций.

4. **Логирование**: Детальное логирование всех операций с эмодзи для удобства отладки:
   ✅ - успешные операции
   ❌ - ошибки
   ⚠️ - предупреждения
   🔍 - операции поиска

5. **Типизация**: Полная поддержка type hints для IDE и статических анализаторов.

Структура CRUD операций:
-------------------------
- **Product**: Create, Read (by id/all), Update, Delete, Search (advanced/like)
- **Category**: Create, Read (by id/all), Update, Delete
- **Tag**: Create, Read (by id/all), Update, Delete

Особенности работы со связями:
-------------------------------
- **O2M (Product → Category)**: FK связь с ondelete="SET NULL"
- **M2M (Product ↔ Tag)**: Ассоциативная таблица с ondelete="CASCADE"

Транзакционная безопасность:
-----------------------------
Все модифицирующие операции (Create, Update, Delete) используют декоратор @with_transaction,
который гарантирует:
- Автоматический commit при успешном выполнении
- Автоматический rollback при любых исключениях
- Детальное логирование ошибок с трейсбеком
"""

from sqlalchemy import create_engine, select, or_
from sqlalchemy.orm import sessionmaker, selectinload, Session
from models.models import Product as ProductORM, Category as CategoryORM, Tag as TagORM
from config import settings
from schemas.schemas import (
    ProductCreate,
    Product,
    CategoryCreate,
    Category,
    TagCreate,
    Tag,
    ProductUpdate,
)
import logging
from functools import wraps
from typing import TypeVar, Callable

# Создаём именованный логгер для этого модуля
logger = logging.getLogger(__name__)

# Type variables для декоратора
T = TypeVar("T")


def with_transaction(func: Callable[..., T]) -> Callable[..., T]:
    """
    Декоратор для автоматической обработки транзакций SQLAlchemy.

    Оборачивает функцию в транзакцию с автоматическим управлением:
    - Создаёт сессию из session_local (первый аргумент функции)
    - Автоматически выполняет commit() при успешном завершении
    - Автоматически выполняет rollback() при любых исключениях
    - Логирует ошибки с полным трейсбеком

    Использование:
    --------------
    @with_transaction
    def my_crud_function(session: Session, arg1, arg2):
        # session уже создана декоратором
        # работаем с БД
        # commit произойдёт автоматически
        return result

    # Вызов (передаём session_local, декоратор создаст session):
    my_crud_function(SessionLocal, value1, value2)

    :param func: Функция для оборачивания
    :return: Обёрнутая функция с управлением транзакциями
    """

    @wraps(func)
    def wrapper(session_local: sessionmaker, *args, **kwargs) -> T:
        with session_local() as session:
            try:
                # Вызываем функцию, передавая session вместо session_local
                result = func(session, *args, **kwargs)
                session.commit()
                return result
            except Exception as e:
                session.rollback()
                logger.error(f"❌ Ошибка в {func.__name__}: {e}", exc_info=True)
                raise

    return wrapper


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


@with_transaction
def product_delete_by_id(session: Session, product_id: int) -> int:
    """
    Удаляет продукт по ID с явной загрузкой связей.

    :param session: Сессия SQLAlchemy (передаётся декоратором).
    :param product_id: ID продукта для удаления.
    :return: ID удалённого продукта или -1 при ошибке

    Особенности:
    - Загружает категорию и теги перед удалением (требуется из-за lazy="raise_on_sql")
    - M2M связи с тегами удаляются автоматически благодаря CASCADE
    - O2M связь с категорией обработана через ondelete="SET NULL"
    """
    # Загружаем продукт со всеми связями
    stmt = (
        select(ProductORM)
        .where(ProductORM.id == product_id)
        .options(selectinload(ProductORM.category), selectinload(ProductORM.tags))
    )

    product = session.execute(stmt).scalar_one_or_none()

    if not product:
        logger.warning(f"❌ Продукт с ID={product_id} не найден для удаления.")
        return -1

    # Явно очищаем M2M связь (опционально, CASCADE делает это автоматически)
    product.tags.clear()

    session.delete(product)
    # Commit выполнится автоматически декоратором

    logger.info(
        f"✅ Продукт '{product.name}' (ID={product_id}) успешно удалён. "
        f"Категория: {product.category.name if product.category else 'Нет'}"
    )
    return product_id


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


@with_transaction
def category_create(session: Session, category_data: CategoryCreate) -> Category:
    """
    Создание новой категории.

    :param session: Сессия SQLAlchemy (передаётся декоратором).
    :param category_data: Данные для создания категории
    :return: Category с id и name категории
    """
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
    session.flush()
    session.refresh(new_category)

    result = Category.model_validate(new_category)
    logger.info(f"✅ Категория создана: ID={result.id}, Name={result.name}")
    return result


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


@with_transaction
def category_update(session: Session, category_id: int, name: str) -> Category:
    """
    Обновление категории по ID.

    :param session: Сессия SQLAlchemy (передаётся декоратором).
    :param category_id: ID категории для обновления.
    :param name: Новое имя категории.
    :return: Category с обновлёнными данными
    :raises ValueError: Если категория не найдена
    """
    category = session.get(CategoryORM, category_id)

    if not category:
        error_msg = f"Категория с ID={category_id} не найдена"
        logger.error(f"❌ {error_msg}")
        raise ValueError(error_msg)

    # Обновляем имя
    category.name = name
    # flush - фиксируем изменения в сессии
    session.flush()

    # refresh - обновляем объект из базы данных
    session.refresh(category)

    result = Category.model_validate(category)
    logger.info(f"✅ Категория обновлена: ID={category_id}, Name={name}")
    return result


@with_transaction
def category_delete(session: Session, category_id: int) -> int:
    """
    Удаление категории с проверкой зависимых продуктов.

    :param session: Сессия SQLAlchemy (передаётся декоратором).
    :param category_id: ID категории для удаления.
    :return: ID удалённой категории или -1 при ошибке

    ⚠️ ВАЖНО: При ondelete="SET NULL" продукты останутся, но потеряют категорию!
    """
    # Проверяем наличие связанных продуктов
    stmt = select(ProductORM).where(ProductORM.category_id == category_id)
    products = session.execute(stmt).scalars().all()
    products_count = len(products)

    if products_count > 0:
        logger.warning(
            f"⚠️ У категории {category_id} есть {products_count} продуктов. "
            f"Они станут без категории (category_id = NULL)."
        )

    category = session.get(CategoryORM, category_id)
    if not category:
        logger.warning(f"❌ Категория с ID={category_id} не найдена")
        return -1

    session.delete(category)
    # Commit выполнится автоматически декоратором

    logger.info(
        f"✅ Категория ID={category_id} удалена. "
        f"Продуктов осталось без категории: {products_count}"
    )
    return category_id


# ============================================
# CRUD для Tag
# ============================================


@with_transaction
def tag_create(session: Session, tag_data: TagCreate) -> Tag:
    """
    Создание нового тега.

    :param session: Сессия SQLAlchemy (передаётся декоратором).
    :param tag_data: Данные для создания тега
    :return: Tag с id и name тега
    """
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
    session.flush()
    session.refresh(new_tag)

    result = Tag.model_validate(new_tag)
    logger.info(f"✅ Тег создан: ID={result.id}, Name={result.name}")
    return result


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


@with_transaction
def tag_update(session: Session, tag_id: int, name: str) -> Tag:
    """
    Обновление тега по ID.

    :param session: Сессия SQLAlchemy (передаётся декоратором).
    :param tag_id: ID тега для обновления.
    :param name: Новое имя тега.
    :return: Tag с обновлёнными данными
    :raises ValueError: Если тег не найден
    """
    tag = session.get(TagORM, tag_id)

    if not tag:
        error_msg = f"Тег с ID={tag_id} не найден"
        logger.error(f"❌ {error_msg}")
        raise ValueError(error_msg)

    # Обновляем имя
    tag.name = name
    session.flush()
    session.refresh(tag)

    result = Tag.model_validate(tag)
    logger.info(f"✅ Тег обновлён: ID={tag_id}, Name={name}")
    return result


@with_transaction
def tag_delete(session: Session, tag_id: int) -> int:
    """
    Удаление тега (M2M связь безопасна благодаря CASCADE).

    :param session: Сессия SQLAlchemy (передаётся декоратором).
    :param tag_id: ID тега для удаления.
    :return: ID удалённого тега или -1 при ошибке

    Особенности:
    - M2M связи с продуктами удаляются автоматически благодаря CASCADE
    - Продукты остаются в БД, удаляются только записи в ассоциативной таблице
    """
    # Загружаем тег со связями для подсчёта
    stmt = (
        select(TagORM).where(TagORM.id == tag_id).options(selectinload(TagORM.products))
    )
    tag = session.execute(stmt).scalar_one_or_none()

    if not tag:
        logger.warning(f"❌ Тег с ID={tag_id} не найден")
        return -1

    # Подсчёт связанных продуктов для логирования
    products_count = len(tag.products)

    session.delete(tag)
    # Commit выполнится автоматически декоратором

    logger.info(
        f"✅ Тег ID={tag_id} удалён. Удалено связей с продуктами: {products_count}"
    )
    return tag_id


# ============================================
# CRUD для Product
# ============================================


@with_transaction
def product_create(
    session: Session,
    product_data: ProductCreate,
) -> Product:
    """
    Создание нового продукта со связями (категория и теги).

    :param session: Сессия SQLAlchemy (передаётся декоратором).
    :param product_data: Данные продукта (ProductCreate) с category_id и tag_ids
    :return: Product с данными созданного продукта

    Особенности:
    - Строгая валидация: отсутствие категории или тегов вызовет ValueError
    - M2M связь с тегами устанавливается через список объектов
    - O2M связь с категорией через объект (category_id устанавливается автоматически)
    """
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
            raise ValueError(error_msg)

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
            raise ValueError(error_msg)

        # Устанавливаем связь M2M
        new_product.tags = list(tags_orm)

    # 4. Сохраняем продукт
    session.add(new_product)
    session.flush()  # Применяем изменения для получения ID

    # 5. Перезагружаем с полными связями для возврата
    stmt = (
        select(ProductORM)
        .where(ProductORM.id == new_product.id)
        .options(selectinload(ProductORM.category), selectinload(ProductORM.tags))
    )
    refreshed_product = session.execute(stmt).scalar_one()

    result = Product.model_validate(refreshed_product)

    logger.info(
        f"✅ Продукт создан: ID={result.id}, "
        f"Category={result.category.name if result.category else 'Нет'}, "
        f"Tags={[tag.name for tag in result.tags]}"
    )
    return result


def product_get_by_id(session_local: sessionmaker, product_id: int) -> Product | None:
    """
    Получает продукт по ID с загрузкой категории и тегов.

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


def product_get_all(
    session_local: sessionmaker, skip: int = 0, limit: int = 100
) -> list[Product]:
    """
    Получить все продукты с категориями и тегами.

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


def product_search_advanced(
    session_local: sessionmaker, search: str, skip: int = 0, limit: int = 100
) -> list[Product]:
    """
    Расширенный поиск продуктов по названию, категории или тегам.

    :param session_local: Фабрика сессий SQLAlchemy.
    :param search: Поисковый запрос
    :param skip: Количество записей для пропуска (пагинация)
    :param limit: Максимальное количество записей (пагинация)
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
            .offset(skip)
            .limit(limit)
        )

        products = session.execute(stmt).scalars().unique().all()

        result = [Product.model_validate(p) for p in products]
        logger.info(f"✅ Найдено продуктов: {len(result)}")
        return result


@with_transaction
def product_update(session: Session, product_data: ProductUpdate) -> Product:
    """
    Обновление существующего продукта со связями (категория и теги).

    :param session: Сессия SQLAlchemy (передаётся декоратором).
    :param product_data: Данные продукта (ProductUpdate) с category_id и tag_ids
    :return: Product с данными обновлённого продукта
    """
    # 1. Получаем существующий продукт
    existing_product = session.get(ProductORM, product_data.id)
    if not existing_product:
        error_msg = f"Продукт с ID {product_data.id} не найден для обновления"
        logger.error(f"❌ {error_msg}")
        raise ValueError(error_msg)

    # 2. Обновляем поля продукта через распаковку DTO
    product_dict = product_data.model_dump(exclude={"category_id", "tag_ids"})
    for key, value in product_dict.items():
        setattr(existing_product, key, value)

    # 3. Обрабатываем категорию (FK связь)
    if product_data.category_id is not None:
        logger.info(f"Обновление категории ID: {product_data.category_id}")

        # Получаем категорию по ID
        category_orm = session.get(CategoryORM, product_data.category_id)

        # Если её нет, выбрасываем ошибку
        if not category_orm:
            error_msg = f"Категория с ID {product_data.category_id} не найдена"
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)

        # Привязываем через объект (SQLAlchemy автоматически установит category_id)
        existing_product.category = category_orm
    else:
        # Если category_id None, отвязываем категорию
        existing_product.category = None

    # 4. Обрабатываем теги (M2M связь)
    if product_data.tag_ids is not None:
        logger.info(f"Обновление тегов: {product_data.tag_ids}")

        # Загружаем все теги одним запросом
        tags_stmt = select(TagORM).where(TagORM.id.in_(product_data.tag_ids))
        tags_orm = session.execute(tags_stmt).scalars().all()

        # Проверяем, что все теги найдены
        found_ids = {tag.id for tag in tags_orm}
        missing_ids = set(product_data.tag_ids) - found_ids

        if missing_ids:
            error_msg = f"Теги с ID {missing_ids} не найдены"
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)

        # Устанавливаем связь M2M
        existing_product.tags = list(tags_orm)
    else:
        # Если tag_ids None, очищаем теги
        existing_product.tags = []

    # 5. Сохраняем изменения продукта
    session.flush()
    session.refresh(existing_product)

    # 6. Возвращаем с полными связями
    result = Product.model_validate(existing_product)
    logger.info(
        f"✅ Продукт обновлён: ID={result.id}, "
        f"Category={result.category.name if result.category else 'Нет'}, "
        f"Tags={[tag.name for tag in result.tags]}"
    )
    return result
