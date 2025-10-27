"""
Главная точка входа приложения.
"""

# ✅ ПЕРВЫМ ДЕЛОМ настраиваем логирование!
from utils.logger import setup_logging
import logging

# Настройка логирования (вызываем ОДИН РАЗ при старте)
setup_logging()

# Теперь можем импортировать остальные модули
from utils.db_operations import get_engine, get_session_factory, product_create
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


if __name__ == "__main__":
    main()
