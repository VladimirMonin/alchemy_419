"""
Модуль настройки логирования для всего приложения.
Импортировать этот модуль в main.py для инициализации.
"""

import logging


def setup_logging(
    level=logging.INFO, log_file="app.log", sqlalchemy_log_file="sqlalchemy.log"
):
    """
    Настраивает корневой логгер для всего приложения.

    :param level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    :param log_file: Путь к файлу логов приложения
    :param sqlalchemy_log_file: Путь к файлу логов SQLAlchemy
    """
    # Настройка корневого логгера для приложения
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    # Настройка отдельного логгера для SQLAlchemy
    sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
    sqlalchemy_logger.setLevel(logging.INFO)  # Уровень для SQL запросов

    # Убираем стандартные обработчики (чтобы не дублировалось в app.log)
    sqlalchemy_logger.propagate = False

    # Добавляем свой обработчик для SQLAlchemy
    sqlalchemy_handler = logging.FileHandler(sqlalchemy_log_file, encoding="utf-8")
    sqlalchemy_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    sqlalchemy_logger.addHandler(sqlalchemy_handler)

    # Опционально: выводить SQL в консоль (закомментируйте если не нужно)
    sqlalchemy_console = logging.StreamHandler()
    sqlalchemy_console.setFormatter(logging.Formatter("🗄️ SQL: %(message)s"))
    sqlalchemy_logger.addHandler(sqlalchemy_console)

    logging.info("Логирование настроено")
    logging.info(f"SQL логи сохраняются в: {sqlalchemy_log_file}")


def setup_debug_logging():
    """Подробное логирование для разработки."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("debug.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    # SQLAlchemy с максимальной детализацией
    sqlalchemy_logger = logging.getLogger("sqlalchemy")
    sqlalchemy_logger.setLevel(logging.DEBUG)
    sqlalchemy_logger.propagate = False

    sqlalchemy_handler = logging.FileHandler("sqlalchemy_debug.log", encoding="utf-8")
    sqlalchemy_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    sqlalchemy_logger.addHandler(sqlalchemy_handler)

    logging.info("Debug логирование настроено")


def setup_production_logging():
    """Минимальное логирование для продакшена."""
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("production.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    # В продакшене SQLAlchemy логи отключаем или минимизируем
    sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
    sqlalchemy_logger.setLevel(logging.WARNING)  # Только ошибки
    sqlalchemy_logger.propagate = False

    logging.info("Production логирование настроено")


def setup_custom_sqlalchemy_logging(
    sql_log_file="sql_queries.log", sql_level=logging.INFO, include_params=True
):
    """
    Детальная настройка логирования SQLAlchemy.

    :param sql_log_file: Файл для SQL запросов
    :param sql_level: Уровень логирования SQL
    :param include_params: Логировать параметры запросов
    """
    # Логгер для SQL запросов
    sql_logger = logging.getLogger("sqlalchemy.engine")
    sql_logger.setLevel(sql_level)
    sql_logger.propagate = False

    sql_handler = logging.FileHandler(sql_log_file, encoding="utf-8")
    sql_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    sql_logger.addHandler(sql_handler)

    if include_params:
        # Логгер для параметров запросов
        params_logger = logging.getLogger("sqlalchemy.engine.base.Engine")
        params_logger.setLevel(logging.DEBUG)
        params_logger.propagate = False
        params_logger.addHandler(sql_handler)

    logging.info(f"SQLAlchemy логи настроены: {sql_log_file}")
