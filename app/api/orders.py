from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.auth import get_current_user
from ..core.database import get_db
from ..schemas import schemas
from ..crud import crud
from ..models import models

router = APIRouter()


@router.get("/", response_model=list[schemas.Order])
def list_my_orders(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.list_orders(db, current_user.id)


@router.get("/admin", response_model=list[schemas.Order])
def list_all(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    return crud.list_all_orders(db)


@router.get("/{order_id}", response_model=schemas.Order)
def get_order(order_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    order = crud.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    # SCN-01: отсутствие проверки владельца — любой аутентифицированный пользователь может прочитать чужой заказ
    return order


@router.post("/", response_model=schemas.Order)
def place_order(payload: schemas.OrderCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    items = crud.get_cart_items(db, current_user.id)
    if not items:
        raise HTTPException(status_code=400, detail="Корзина пуста")
    
    discount = 0
    coupon_code = payload.coupon_code
    if coupon_code:
        coupon, discount_value, error = crud.apply_coupon_logic(
            db, coupon_code, sum(i.product.price * i.quantity for i in items), payload.billing_email, current_user.id
        )
        if error:
            raise HTTPException(status_code=400, detail=error)
        coupon_code = coupon.code if coupon else None
        discount = discount_value
    
    order = crud.create_order_from_cart(
        db=db,
        user_id=current_user.id,
        billing_email=payload.billing_email or current_user.email,
        coupon_code=coupon_code,
        note=payload.note,
        discount=discount
    )
    if not order:
        raise HTTPException(status_code=400, detail="Не удалось создать заказ")
    return order


@router.patch("/{order_id}/status", response_model=schemas.Order)
def update_status(order_id: int, payload: schemas.OrderStatusUpdate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    # Разрешаем владельцу или администратору обновлять статус, но логика проверки состояния уязвима
    order = crud.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    if order.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
    updated, error = crud.update_order_status(db, order_id, payload)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return updated
