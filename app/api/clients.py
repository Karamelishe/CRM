from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.auth import get_current_active_user
from ..crud import crud
from ..schemas import schemas

router = APIRouter()


@router.get("/", response_model=List[schemas.Client])
def read_clients(
    skip: int = 0,
    limit: int = 100,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получить список клиентов"""
    clients = crud.get_clients(db, owner_id=current_user.id, skip=skip, limit=limit)
    return clients


@router.post("/", response_model=schemas.Client)
def create_client(
    client: schemas.ClientCreate,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Создать нового клиента"""
    # Проверяем, не существует ли клиент с таким телефоном
    db_client = crud.get_client_by_phone(db, phone=client.phone, owner_id=current_user.id)
    if db_client:
        raise HTTPException(status_code=400, detail="Клиент с таким телефоном уже существует")
    
    return crud.create_client(db=db, client=client, owner_id=current_user.id)


@router.get("/{client_id}", response_model=schemas.Client)
def read_client(
    client_id: int,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получить клиента по ID"""
    db_client = crud.get_client(db, client_id=client_id, owner_id=current_user.id)
    if db_client is None:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    return db_client


@router.put("/{client_id}", response_model=schemas.Client)
def update_client(
    client_id: int,
    client: schemas.ClientUpdate,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Обновить данные клиента"""
    db_client = crud.update_client(db, client_id=client_id, client=client, owner_id=current_user.id)
    if db_client is None:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    return db_client


@router.delete("/{client_id}")
def delete_client(
    client_id: int,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Удалить клиента"""
    db_client = crud.delete_client(db, client_id=client_id, owner_id=current_user.id)
    if db_client is None:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    return {"message": "Клиент удален"}