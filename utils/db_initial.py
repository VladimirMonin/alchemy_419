# utils/db_initial.py
"""
Модуль инициализации базы данных
"""
from models.base import Base
from utils.db_operations import get_engine
import logging

# Создаём именованный логгер для этого модуля
logger = logging.getLogger(__name__)


def create_tables():
    """Создаёт все таблицы в БД на основе моделей."""
    logger.info("Начало создания таблиц...")
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Таблицы успешно созданы!")


def drop_tables():
    """Удаляет все таблицы из БД. ОСТОРОЖНО: удалит все данные!"""
    logger.warning("⚠️ Запрос на удаление ВСЕХ таблиц!")
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    logger.info("🗑️ Таблицы удалены!")
