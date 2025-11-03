"""
Главная точка входа приложения.
"""

# ✅ ПЕРВЫМ ДЕЛОМ настраиваем логирование!
from utils.logger import setup_logging
import logging

# Настройка логирования (вызываем ОДИН РАЗ при старте)
setup_logging(
    level=logging.INFO,
    log_file="./logs/app.log",
    sqlalchemy_log_file="./logs/sqlalchemy.log",
)

# Теперь можем импортировать остальные модули
from utils.db_operations import (
    get_engine,
    get_session_factory,
    category_create,
    category_get_all,
    tag_create,
    tag_get_all,
    product_create_with_relations,
    product_get_all_with_relations,
    product_search_advanced,
)
from utils.db_initial import create_tables
from schemas.schemas import ProductCreate, CategoryCreate, TagCreate

# Логгер для main
logger = logging.getLogger(__name__)


def main():
    logger.info("=" * 50)
    logger.info("Запуск приложения...")
    logger.info("=" * 50)

    # Создаём engine и session factory
    engine = get_engine()
    SessionLocal = get_session_factory(engine)

    # Создаём таблицы
    create_tables()

    # Работаем с БД
    logger.info("\n" + "=" * 50)
    logger.info("Создание категорий")
    logger.info("=" * 50)

    # 1. Создаём категории
    electronics = category_create(SessionLocal, CategoryCreate(name="Электроника"))
    gadgets = category_create(SessionLocal, CategoryCreate(name="Гаджеты"))
    food = category_create(SessionLocal, CategoryCreate(name="Еда"))

    logger.info("\n" + "=" * 50)
    logger.info("Создание тегов")
    logger.info("=" * 50)

    # 2. Создаём теги
    new_tag = tag_create(SessionLocal, TagCreate(name="Новинка"))
    sale_tag = tag_create(SessionLocal, TagCreate(name="Скидка"))
    popular_tag = tag_create(SessionLocal, TagCreate(name="Популярное"))
    premium_tag = tag_create(SessionLocal, TagCreate(name="Премиум"))

    logger.info("\n" + "=" * 50)
    logger.info("Создание продуктов со связями")
    logger.info("=" * 50)

    # 3. Создаём продукты со связями
    product1 = product_create_with_relations(
        SessionLocal,
        ProductCreate(
            name="Плюмбус",
            description="Незаменимая вещь в каждом доме",
            image_url="https://example.com/plumbus.jpg",
            price_shmeckles=25.5,
            price_flurbos=3.2,
            category_id=electronics.id,
            tag_ids=[new_tag.id, popular_tag.id],
        ),
    )

    product2 = product_create_with_relations(
        SessionLocal,
        ProductCreate(
            name="Портальная пушка",
            description="Открывает порталы между измерениями",
            price_shmeckles=1000.0,
            price_flurbos=150.0,
            category_id=gadgets.id,
            tag_ids=[new_tag.id, sale_tag.id, premium_tag.id],
        ),
    )

    product3 = product_create_with_relations(
        SessionLocal,
        ProductCreate(
            name="Мега-семена",
            description="Семена из измерения C-137",
            price_shmeckles=50.0,
            price_flurbos=7.5,
            category_id=food.id,
            tag_ids=[popular_tag.id],
        ),
    )

    product4 = product_create_with_relations(
        SessionLocal,
        ProductCreate(
            name="Флиббо-джиббер",
            description="Устройство для флиббования",
            price_shmeckles=75.0,
            price_flurbos=12.0,
            # Без категории!
            tag_ids=[premium_tag.id],
        ),
    )

    logger.info("\n" + "=" * 50)
    logger.info("Все категории в БД:")
    logger.info("=" * 50)

    all_categories = category_get_all(SessionLocal)
    for cat in all_categories:
        logger.info(f"  • {cat.name} (ID: {cat.id})")

    logger.info("\n" + "=" * 50)
    logger.info("Все теги в БД:")
    logger.info("=" * 50)

    all_tags = tag_get_all(SessionLocal)
    for tag in all_tags:
        logger.info(f"  • {tag.name} (ID: {tag.id})")

    logger.info("\n" + "=" * 50)
    logger.info("Все продукты в БД:")
    logger.info("=" * 50)

    # Получаем все продукты
    all_products = product_get_all_with_relations(SessionLocal)
    for product in all_products:
        logger.info(
            f"\n📦 {product.name} ({product.price_shmeckles} шмеклей)\n"
            f"   Категория: {product.category.name if product.category else '❌ Без категории'}\n"
            f"   Теги: {', '.join(tag.name for tag in product.tags) if product.tags else '❌ Без тегов'}"
        )

    logger.info("\n" + "=" * 50)
    logger.info("Расширенный поиск по слову 'портал':")
    logger.info("=" * 50)

    # Поиск по названию, категории и тегам
    search_results = product_search_advanced(SessionLocal, "портал")
    for product in search_results:
        logger.info(f"  ✅ Найдено: {product.name}")

    logger.info("\n" + "=" * 50)
    logger.info("Поиск по слову 'новинка' (тег):")
    logger.info("=" * 50)

    search_results = product_search_advanced(SessionLocal, "новинка")
    for product in search_results:
        logger.info(f"  ✅ Найдено: {product.name}")


if __name__ == "__main__":
    main()
