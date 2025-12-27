from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.auth import get_current_user
from ..schemas import schemas
from ..crud import crud

router = APIRouter()


@router.get("/", response_model=list[schemas.Product])
def list_storefront_products(db: Session = Depends(get_db)):
    return crud.list_products(db, active_only=True)


@router.get("/all", response_model=list[schemas.Product])
def list_all_products(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Только администратор может просматривать все товары")
    return crud.list_products(db, active_only=False)


@router.post("/", response_model=schemas.Product)
def create_product(product: schemas.ProductCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    return crud.create_product(db, product)


@router.put("/{product_id}", response_model=schemas.Product)
def update_product(product_id: int, product: schemas.ProductUpdate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    updated = crud.update_product(db, product_id, product)
    if not updated:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return updated


@router.delete("/{product_id}")
def delete_product(product_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    deleted = crud.delete_product(db, product_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return {"detail": "Удалено"}
