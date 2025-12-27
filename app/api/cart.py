from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.auth import get_current_user
from ..core.database import get_db
from ..schemas import schemas
from ..crud import crud

router = APIRouter()


@router.get("/", response_model=schemas.CartSummary)
def get_cart(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    items = crud.get_cart_items(db, current_user.id)
    subtotal = sum(item.product.price * item.quantity for item in items)
    return schemas.CartSummary(items=items, subtotal=subtotal, total=subtotal, discount=0)


@router.post("/add", response_model=schemas.CartItem)
def add_item(payload: schemas.CartItemCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    item = crud.add_to_cart(db, current_user.id, payload.product_id, payload.quantity)
    if not item:
        raise HTTPException(status_code=404, detail="Товар не найден или недоступен")
    return item


@router.put("/item/{item_id}", response_model=schemas.CartItem)
def update_item(item_id: int, payload: schemas.CartItemCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    item = crud.update_cart_item(db, item_id, current_user.id, payload.quantity)
    if not item:
        raise HTTPException(status_code=404, detail="Позиция не найдена")
    return item


@router.delete("/item/{item_id}")
def delete_item(item_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    deleted = crud.remove_cart_item(db, item_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Позиция не найдена")
    return {"detail": "Удалено"}


@router.post("/apply-coupon")
def apply_coupon(payload: schemas.CouponApplyRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    coupon, discount, error = crud.apply_coupon_logic(
        db, payload.code, payload.cart_total, payload.billing_email, current_user.id
    )
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {
        "discount": discount,
        "applied_coupon": coupon.code if coupon else None,
        "message": "Купон применен"
    }
