"""
Конфигурация приложения через Pydantic Settings
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения"""

    db_name: str = "products.db"
    db_echo: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Единственный экземпляр настроек
settings = Settings()
