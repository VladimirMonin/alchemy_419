"""
Главная точка входа приложения.
"""

from utils.db_operations import get_engine, get_session_factory, product_create
from utils.db_initial import init_db

if __name__ == "__main__":
    # Инициализация базы данных
    init_db()

    engine = get_engine()
    SessionLocal = get_session_factory(engine)

    # Пример создания продукта
    product = product_create(
        session_local=SessionLocal,
        name="Портальная пушка Рика. Б\у",
        description="Отличная портальная пушка, бывшая в употреблении. Работает без нареканий. Заряда жидкости 52%",
        image_url="http://rick-morty.com/portal_gun.png",
        price_shmeckles=1900.99,
        price_flurbos=200.99,
    )
    print(f"Создан продукт: {product}")
