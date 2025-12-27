#!/usr/bin/env python3
"""
Инициализация лабораторного магазина:
- Создает таблицы
- Добавляет пользователей, товары, купоны и предсозданные заказы с флагами
"""

from sqlalchemy.orm import Session
from app.core.database import engine, Base
from app.crud import crud
from app.schemas import schemas
from app.models import models


def init_database():
    print("Создание таблиц...")
    Base.metadata.create_all(bind=engine)
    print("Таблицы созданы.")
    
    db = Session(bind=engine)
    try:
        if crud.get_user_by_email(db, "admin@shop.local"):
            print("База уже инициализирована.")
            return
        
        # Пользователи
        admin = crud.create_user(db, schemas.UserCreate(
            email="admin@shop.local",
            password="admin123",
            full_name="Лабораторный админ"
        ))
        admin.is_admin = True
        
        alice = crud.create_user(db, schemas.UserCreate(
            email="alice@shop.local",
            password="customer123",
            full_name="Алиса"
        ))
        
        bob = crud.create_user(db, schemas.UserCreate(
            email="bob@shop.local",
            password="customer123",
            full_name="Боб"
        ))
        db.commit()
        
        print("Созданы пользователи: admin@shop.local / alice@shop.local / bob@shop.local (пароль customer123 у клиентов).")
        
        # Товары
        products = [
            schemas.ProductCreate(
                title="Aurora Headphones",
                description="Беспроводные наушники с шумоподавлением и 40ч работы.",
                price=129990,
                stock=15,
                image="https://images.unsplash.com/photo-1518449951450-1a1c1c5dc0a0?auto=format&fit=crop&w=900&q=60"
            ),
            schemas.ProductCreate(
                title="Neon Sneakers",
                description="Ультралегкие кроссовки для городских приключений.",
                price=89990,
                stock=25,
                image="https://images.unsplash.com/photo-1549298916-b41d501d3772?auto=format&fit=crop&w=900&q=60"
            ),
            schemas.ProductCreate(
                title="Skyline Backpack",
                description="Рюкзак с защитой от RFID и USB-портом для зарядки.",
                price=74990,
                stock=30,
                image="https://images.unsplash.com/photo-1522198436769-9ffcb3cb0e43?auto=format&fit=crop&w=900&q=60"
            )
        ]
        created_products = [crud.create_product(db, p) for p in products]
        print(f"Создано товаров: {len(created_products)}")
        
        # Купоны
        coupon = models.Coupon(
            code="ONETIME50",
            description="50% скидка, должна сработать один раз на email",
            discount_type=models.DiscountType.PERCENT,
            value=50,
            min_total=50000,
            max_uses_per_user=1,
            global_limit=50,
            active=True
        )
        db.add(coupon)
        db.commit()
        print("Купон ONETIME50 добавлен.")
        
        # Предсозданный заказ для SCN-01 (принадлежит Алисе)
        order = models.Order(
            user_id=alice.id,
            status=models.OrderStatus.PAID,
            total_amount=created_products[0].price,
            discount_applied=0,
            coupon_code=None,
            note="Только владелец должен видеть это примечание.",
            billing_email="alice@shop.local"
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        db.add(models.OrderItem(
            order_id=order.id,
            product_id=created_products[0].id,
            quantity=1,
            unit_price=created_products[0].price
        ))
        # Скрытый флаг доступен в примечании заказа
        order.lab_flag = "FLAG-SCN01-ECOMMERCE"
        db.commit()
        print(f"Добавлен заказ #{order.id} с флагом SCN-01 (принадлежит alice@shop.local).")
        
        print("\n== Готово ==")
        print("Админ: admin@shop.local / admin123")
        print("Клиенты: alice@shop.local, bob@shop.local (пароль customer123)")
        print("Флаги:")
        print(" SCN-01: спрятан в чужом заказе (доступ к /api/orders/{id})")
        print(" SCN-02: нарушите state machine до REFUNDED")
        print(" SCN-03: обойдите ограничение купона ONETIME50 через billing_email")
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
