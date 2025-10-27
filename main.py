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
    product_create,
    product_update_by_id,
    product_delete_by_id,
    product_get_by_id,
    product_get_all,
)
from utils.db_initial import create_tables

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

    # Создаём тестовый продукт
    try:
        product = product_create(
            session_local=SessionLocal,
            name="Портальная пушка Рика. Б/у",
            description="Отличная портальная пушка, бывшая в употреблении. Работает без нареканий. Заряд жидкости 52%",
            image_url="http://rick-morty.com/portal_gun.png",
            price_shmeckles=1900.99,
            price_flurbos=200.99,
        )
        logger.info(f"Главная функция: получен продукт {product}")

    except Exception as e:
        logger.critical(f"Критическая ошибка в main: {e}", exc_info=True)
        raise

    logger.info("Приложение завершено успешно")

    # Обновляем тестовый продукт (обновим цены)
    try:
        updated_product = product_update_by_id(
            session_local=SessionLocal,
            product_id=product.id,
            price_shmeckles=1800.49,
            price_flurbos=190.49,
        )
        if updated_product:
            logger.info(f"Главная функция: обновлен продукт {updated_product}")
        else:
            logger.error("Главная функция: не удалось обновить продукт")

    except Exception as e:
        logger.critical(
            f"Критическая ошибка при обновлении продукта в main: {e}", exc_info=True
        )
        raise

    # Получаем тестовый продукт по ID
    try:
        fetched_product = product_get_by_id(
            session_local=SessionLocal,
            product_id=product.id,
        )
        if fetched_product:
            logger.info(f"Главная функция: получен продукт по ID {fetched_product}")
        else:
            logger.error("Главная функция: не удалось получить продукт по ID")
    except Exception as e:
        logger.critical(
            f"Критическая ошибка при получении продукта по ID в main: {e}",
            exc_info=True,
        )
        raise

    # Получаем все продукты
    try:
        all_products = product_get_all(session_local=SessionLocal)
        logger.info(f"Главная функция: получены все продукты: {all_products}")
    except Exception as e:
        logger.critical(
            f"Критическая ошибка при получении всех продуктов в main: {e}",
            exc_info=True,
        )
        raise

    # Удаляем тестовый продукт
    try:
        deleted_id = product_delete_by_id(
            session_local=SessionLocal,
            product_id=product.id,
        )
        if deleted_id != -1:
            logger.info(f"Главная функция: удален продукт с ID={deleted_id}")
        else:
            logger.error("Главная функция: не удалось удалить продукт")
    except Exception as e:
        logger.critical(
            f"Критическая ошибка при удалении продукта в main: {e}", exc_info=True
        )
        raise


if __name__ == "__main__":
    main()
