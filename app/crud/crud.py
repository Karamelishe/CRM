from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List
from datetime import datetime
from passlib.context import CryptContext

from ..models import models
from ..schemas import schemas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# User helpers
def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        password_hash=hashed_password,
        full_name=user.full_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        return False
    return user


# Product CRUD
def list_products(db: Session, active_only: bool = True):
    query = db.query(models.Product)
    if active_only:
        query = query.filter(models.Product.is_active == True)
    return query.all()


def get_product(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()


def create_product(db: Session, product: schemas.ProductCreate):
    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def update_product(db: Session, product_id: int, product: schemas.ProductUpdate):
    db_product = get_product(db, product_id)
    if db_product:
        for key, value in product.model_dump(exclude_unset=True).items():
            setattr(db_product, key, value)
        db.commit()
        db.refresh(db_product)
    return db_product


def delete_product(db: Session, product_id: int):
    db_product = get_product(db, product_id)
    if db_product:
        db.delete(db_product)
        db.commit()
    return db_product


# Coupon logic
def get_coupon(db: Session, code: str):
    return db.query(models.Coupon).filter(models.Coupon.code == code).first()


def apply_coupon_logic(db: Session, coupon_code: str, cart_total: int, billing_email: Optional[str], user_id: int):
    coupon = get_coupon(db, coupon_code)
    if not coupon or not coupon.active:
        return None, 0, "Купон не найден или не активен"
    
    # Используем email, переданный клиентом, а не текущего пользователя (лабораторная уязвимость)
    usage_email = billing_email
    user_orders = db.query(models.Order).filter(
        and_(models.Order.coupon_code == coupon_code, models.Order.billing_email == usage_email)
    ).count()
    
    if cart_total < coupon.min_total:
        return None, 0, "Сумма корзины ниже минимальной для купона"
    
    if coupon.times_used >= coupon.global_limit:
        return None, 0, "Купон больше недоступен"
    
    if user_orders >= coupon.max_uses_per_user:
        # Из-за логики по email можно обойти ограничение, что и является SCN-03
        return coupon, 0, "Купон уже использован с этим email"
    
    if coupon.discount_type == models.DiscountType.PERCENT:
        discount = int(cart_total * (coupon.value / 100))
    else:
        discount = int(coupon.value * 100)
    
    return coupon, discount, None


# Cart CRUD
def get_cart_items(db: Session, user_id: int):
    return db.query(models.CartItem).filter(models.CartItem.user_id == user_id).all()


def add_to_cart(db: Session, user_id: int, product_id: int, quantity: int = 1):
    product = get_product(db, product_id)
    if not product or not product.is_active:
        return None
    
    item = db.query(models.CartItem).filter(
        and_(models.CartItem.user_id == user_id, models.CartItem.product_id == product_id)
    ).first()
    
    if item:
        item.quantity += quantity
    else:
        item = models.CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
        db.add(item)
    
    db.commit()
    db.refresh(item)
    return item


def update_cart_item(db: Session, item_id: int, user_id: int, quantity: int):
    item = db.query(models.CartItem).filter(
        and_(models.CartItem.id == item_id, models.CartItem.user_id == user_id)
    ).first()
    if item:
        item.quantity = max(1, quantity)
        db.commit()
        db.refresh(item)
    return item


def remove_cart_item(db: Session, item_id: int, user_id: int):
    item = db.query(models.CartItem).filter(
        and_(models.CartItem.id == item_id, models.CartItem.user_id == user_id)
    ).first()
    if item:
        db.delete(item)
        db.commit()
    return item


def clear_cart(db: Session, user_id: int):
    db.query(models.CartItem).filter(models.CartItem.user_id == user_id).delete()
    db.commit()


# Order CRUD
def create_order_from_cart(
    db: Session,
    user_id: int,
    billing_email: Optional[str],
    coupon_code: Optional[str],
    note: Optional[str],
    discount: int
):
    items = get_cart_items(db, user_id)
    if not items:
        return None
    
    total = sum(item.quantity * item.product.price for item in items)
    order = models.Order(
        user_id=user_id,
        status=models.OrderStatus.CREATED,
        total_amount=total - discount,
        discount_applied=discount,
        coupon_code=coupon_code,
        billing_email=billing_email,
        note=note
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    
    for item in items:
        order_item = models.OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.product.price
        )
        db.add(order_item)
    db.commit()
    
    # Увеличиваем счетчик купона, если он применялся
    if coupon_code:
        coupon = get_coupon(db, coupon_code)
        if coupon:
            coupon.times_used += 1
            db.commit()
            repeat_by_user = db.query(models.Order).filter(
                and_(models.Order.user_id == user_id, models.Order.coupon_code == coupon_code, models.Order.id != order.id)
            ).count()
            # SCN-03: повторное использование одноразового купона одним пользователем через манипуляцию billing_email
            if coupon.max_uses_per_user == 1 and repeat_by_user:
                order.lab_flag = "FLAG-SCN03-ECOMMERCE"
            db.commit()
    
    clear_cart(db, user_id)
    db.refresh(order)
    return order


def list_orders(db: Session, user_id: int):
    return db.query(models.Order).filter(models.Order.user_id == user_id).all()


def list_all_orders(db: Session):
    return db.query(models.Order).all()


def get_order_by_id(db: Session, order_id: int):
    # SCN-01: намеренно отсутствует проверка владельца
    return db.query(models.Order).filter(models.Order.id == order_id).first()


def get_order_for_user(db: Session, order_id: int, user_id: int):
    return db.query(models.Order).filter(
        and_(models.Order.id == order_id, models.Order.user_id == user_id)
    ).first()


def update_order_status(db: Session, order_id: int, payload: schemas.OrderStatusUpdate):
    order = get_order_by_id(db, order_id)
    if not order:
        return None, "Order not found"
    
    allowed = {
        models.OrderStatus.CREATED: [models.OrderStatus.PAID],
        models.OrderStatus.PAID: [models.OrderStatus.SHIPPED],
        models.OrderStatus.SHIPPED: [models.OrderStatus.DELIVERED],
        models.OrderStatus.DELIVERED: [models.OrderStatus.REFUNDED],
    }
    
    # Ошибка бизнес-логики: проверяем последовательность по предоставленному клиентом статусу,
    # а не по фактическому статусу заказа.
    expected = allowed.get(payload.from_status, [])
    if payload.to_status not in expected:
        # Нарушение последовательности – выдаем лабораторный флаг при попытке отката к REFUNDED
        if payload.to_status == models.OrderStatus.REFUNDED:
            order.status = payload.to_status
            order.lab_flag = "FLAG-SCN02-ECOMMERCE"
            db.commit()
            db.refresh(order)
            return order, None
        return None, "Недопустимый переход"
    
    order.status = payload.to_status
    db.commit()
    db.refresh(order)
    return order, None
