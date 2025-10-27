"""
Модуль настройки логирования для всего приложения.
Импортировать этот модуль в main.py для инициализации.
"""

import logging


def setup_logging(level=logging.INFO, log_file="app.log"):
    """
    Настраивает корневой логгер для всего приложения.

    :param level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    :param log_file: Путь к файлу логов
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    logging.info("Логирование настроено")


def setup_debug_logging():
    """Подробное логирование для разработки."""
    setup_logging(level=logging.DEBUG, log_file="debug.log")


def setup_production_logging():
    """Минимальное логирование для продакшена."""
    setup_logging(level=logging.WARNING, log_file="production.log")
