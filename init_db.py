#!/usr/bin/env python3
"""
Скрипт инициализации базы данных
Создает таблицы и добавляет базовые данные
"""

import asyncio
from sqlalchemy.orm import Session
from app.core.database import engine, Base
from app.core.config import settings
from app.crud import crud
from app.schemas import schemas


def init_database():
    """Инициализация базы данных"""
    print("Создание таблиц...")
    Base.metadata.create_all(bind=engine)
    print("Таблицы созданы!")
    
    # Создаем сессию
    db = Session(bind=engine)
    
    try:
        # Проверяем, есть ли уже пользователи
        existing_user = crud.get_user_by_email(db, "admin@example.com")
        if existing_user:
            print("База данных уже инициализирована!")
            return
        
        # Создаем администратора
        print("Создание пользователя-администратора...")
        admin_user = crud.create_user(db, schemas.UserCreate(
            email="admin@example.com",
            password="admin123",
            full_name="Администратор"
        ))
        
        # Устанавливаем права администратора
        admin_user.is_admin = True
        db.commit()
        
        print(f"Администратор создан: {admin_user.email}")
        
        # Создаем базовые услуги
        print("Создание базовых услуг...")
        services_data = [
            {
                "name": "Консультация",
                "description": "Первичная консультация",
                "duration_minutes": 60,
                "price": 200000  # 2000 рублей в копейках
            },
            {
                "name": "Стрижка",
                "description": "Мужская/женская стрижка",
                "duration_minutes": 45,
                "price": 150000  # 1500 рублей
            },
            {
                "name": "Массаж",
                "description": "Релаксирующий массаж",
                "duration_minutes": 90,
                "price": 350000  # 3500 рублей
            }
        ]
        
        for service_data in services_data:
            service = crud.create_service(db, schemas.ServiceCreate(**service_data))
            print(f"Создана услуга: {service.name}")
        
        # Создаем тестового клиента
        print("Создание тестового клиента...")
        test_client = crud.create_client(db, schemas.ClientCreate(
            full_name="Иван Петров",
            phone="79161234567",
            email="test@example.com",
            telegram_username="test_user",
            notes="Тестовый клиент"
        ), owner_id=admin_user.id)
        
        print(f"Создан клиент: {test_client.full_name}")
        
        print("\n" + "="*50)
        print("База данных успешно инициализирована!")
        print("="*50)
        print("Данные для входа:")
        print(f"Email: admin@example.com")
        print(f"Пароль: admin123")
        print("="*50)
        
    except Exception as e:
        print(f"Ошибка инициализации: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_database()