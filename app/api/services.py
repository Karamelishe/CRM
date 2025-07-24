from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.auth import get_current_active_user
from ..crud import crud
from ..schemas import schemas

router = APIRouter()


@router.get("/", response_model=List[schemas.Service])
def read_services(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Получить список услуг"""
    services = crud.get_services(db, skip=skip, limit=limit)
    return services


@router.post("/", response_model=schemas.Service)
def create_service(
    service: schemas.ServiceCreate,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Создать новую услугу (только для администраторов)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
    return crud.create_service(db=db, service=service)


@router.get("/{service_id}", response_model=schemas.Service)
def read_service(service_id: int, db: Session = Depends(get_db)):
    """Получить услугу по ID"""
    db_service = crud.get_service(db, service_id=service_id)
    if db_service is None:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    return db_service


@router.put("/{service_id}", response_model=schemas.Service)
def update_service(
    service_id: int,
    service: schemas.ServiceUpdate,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Обновить услугу (только для администраторов)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
    db_service = crud.update_service(db, service_id=service_id, service=service)
    if db_service is None:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    return db_service