from typing import List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.auth import get_current_active_user
from ..crud import crud
from ..schemas import schemas

router = APIRouter()


@router.get("/", response_model=List[schemas.Appointment])
def read_appointments(
    skip: int = 0,
    limit: int = 100,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получить список записей"""
    appointments = crud.get_appointments(db, owner_id=current_user.id, skip=skip, limit=limit)
    return appointments


@router.get("/by-date/{target_date}", response_model=List[schemas.Appointment])
def read_appointments_by_date(
    target_date: date,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получить записи на конкретную дату"""
    appointments = crud.get_appointments_by_date(db, owner_id=current_user.id, target_date=target_date)
    return appointments


@router.get("/upcoming", response_model=List[schemas.Appointment])
def read_upcoming_appointments(
    days_ahead: int = Query(default=7, description="Количество дней вперед"),
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получить предстоящие записи"""
    appointments = crud.get_upcoming_appointments(db, owner_id=current_user.id, days_ahead=days_ahead)
    return appointments


@router.post("/", response_model=schemas.Appointment)
def create_appointment(
    appointment: schemas.AppointmentCreate,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Создать новую запись"""
    # Проверяем, что клиент принадлежит текущему пользователю
    client = crud.get_client(db, client_id=appointment.client_id, owner_id=current_user.id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    # Проверяем, что услуга существует
    service = crud.get_service(db, service_id=appointment.service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    
    return crud.create_appointment(db=db, appointment=appointment, owner_id=current_user.id)


@router.get("/{appointment_id}", response_model=schemas.Appointment)
def read_appointment(
    appointment_id: int,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получить запись по ID"""
    db_appointment = crud.get_appointment(db, appointment_id=appointment_id, owner_id=current_user.id)
    if db_appointment is None:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return db_appointment


@router.put("/{appointment_id}", response_model=schemas.Appointment)
def update_appointment(
    appointment_id: int,
    appointment: schemas.AppointmentUpdate,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Обновить запись"""
    db_appointment = crud.update_appointment(
        db, appointment_id=appointment_id, appointment=appointment, owner_id=current_user.id
    )
    if db_appointment is None:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return db_appointment


@router.delete("/{appointment_id}")
def delete_appointment(
    appointment_id: int,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Удалить запись"""
    db_appointment = crud.delete_appointment(db, appointment_id=appointment_id, owner_id=current_user.id)
    if db_appointment is None:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return {"message": "Запись удалена"}