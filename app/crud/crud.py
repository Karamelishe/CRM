from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional
from datetime import datetime, date, timedelta
from passlib.context import CryptContext

from ..models import models
from ..schemas import schemas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# User CRUD
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


# Client CRUD
def get_clients(db: Session, owner_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Client).filter(
        models.Client.owner_id == owner_id
    ).offset(skip).limit(limit).all()


def get_client(db: Session, client_id: int, owner_id: int):
    return db.query(models.Client).filter(
        and_(models.Client.id == client_id, models.Client.owner_id == owner_id)
    ).first()


def get_client_by_phone(db: Session, phone: str, owner_id: int):
    return db.query(models.Client).filter(
        and_(models.Client.phone == phone, models.Client.owner_id == owner_id)
    ).first()


def get_client_by_telegram_id(db: Session, telegram_id: str):
    return db.query(models.Client).filter(
        models.Client.telegram_id == telegram_id
    ).first()


def create_client(db: Session, client: schemas.ClientCreate, owner_id: int):
    db_client = models.Client(**client.model_dump(), owner_id=owner_id)
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client


def update_client(db: Session, client_id: int, client: schemas.ClientUpdate, owner_id: int):
    db_client = get_client(db, client_id, owner_id)
    if db_client:
        for key, value in client.model_dump(exclude_unset=True).items():
            setattr(db_client, key, value)
        db_client.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_client)
    return db_client


def delete_client(db: Session, client_id: int, owner_id: int):
    db_client = get_client(db, client_id, owner_id)
    if db_client:
        db.delete(db_client)
        db.commit()
    return db_client


# Service CRUD
def get_services(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Service).filter(
        models.Service.is_active == True
    ).offset(skip).limit(limit).all()


def get_service(db: Session, service_id: int):
    return db.query(models.Service).filter(models.Service.id == service_id).first()


def create_service(db: Session, service: schemas.ServiceCreate):
    db_service = models.Service(**service.model_dump())
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service


def update_service(db: Session, service_id: int, service: schemas.ServiceUpdate):
    db_service = get_service(db, service_id)
    if db_service:
        for key, value in service.model_dump(exclude_unset=True).items():
            setattr(db_service, key, value)
        db.commit()
        db.refresh(db_service)
    return db_service


# Appointment CRUD
def get_appointments(db: Session, owner_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Appointment).filter(
        models.Appointment.owner_id == owner_id
    ).offset(skip).limit(limit).all()


def get_appointment(db: Session, appointment_id: int, owner_id: int):
    return db.query(models.Appointment).filter(
        and_(models.Appointment.id == appointment_id, models.Appointment.owner_id == owner_id)
    ).first()


def get_appointments_by_date(db: Session, owner_id: int, target_date: date):
    start_of_day = datetime.combine(target_date, datetime.min.time())
    end_of_day = datetime.combine(target_date, datetime.max.time())
    
    return db.query(models.Appointment).filter(
        and_(
            models.Appointment.owner_id == owner_id,
            models.Appointment.datetime >= start_of_day,
            models.Appointment.datetime <= end_of_day
        )
    ).all()


def get_upcoming_appointments(db: Session, owner_id: int, days_ahead: int = 7):
    now = datetime.utcnow()
    future_date = now + timedelta(days=days_ahead)
    
    return db.query(models.Appointment).filter(
        and_(
            models.Appointment.owner_id == owner_id,
            models.Appointment.datetime >= now,
            models.Appointment.datetime <= future_date,
            models.Appointment.status.in_([models.AppointmentStatus.SCHEDULED, models.AppointmentStatus.CONFIRMED])
        )
    ).all()


def create_appointment(db: Session, appointment: schemas.AppointmentCreate, owner_id: int):
    db_appointment = models.Appointment(**appointment.model_dump(), owner_id=owner_id)
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment


def update_appointment(db: Session, appointment_id: int, appointment: schemas.AppointmentUpdate, owner_id: int):
    db_appointment = get_appointment(db, appointment_id, owner_id)
    if db_appointment:
        for key, value in appointment.model_dump(exclude_unset=True).items():
            setattr(db_appointment, key, value)
        db_appointment.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_appointment)
    return db_appointment


def delete_appointment(db: Session, appointment_id: int, owner_id: int):
    db_appointment = get_appointment(db, appointment_id, owner_id)
    if db_appointment:
        db.delete(db_appointment)
        db.commit()
    return db_appointment


# Dashboard stats
def get_dashboard_stats(db: Session, owner_id: int):
    total_clients = db.query(models.Client).filter(
        models.Client.owner_id == owner_id
    ).count()
    
    total_appointments = db.query(models.Appointment).filter(
        models.Appointment.owner_id == owner_id
    ).count()
    
    today = date.today()
    today_appointments = len(get_appointments_by_date(db, owner_id, today))
    
    upcoming_appointments = len(get_upcoming_appointments(db, owner_id, 7))
    
    return schemas.DashboardStats(
        total_clients=total_clients,
        total_appointments=total_appointments,
        today_appointments=today_appointments,
        upcoming_appointments=upcoming_appointments
    )


# Appointments needing reminders
def get_appointments_needing_reminders(db: Session, hours_before: int = 24):
    reminder_time = datetime.utcnow() + timedelta(hours=hours_before)
    
    return db.query(models.Appointment).filter(
        and_(
            models.Appointment.datetime <= reminder_time,
            models.Appointment.datetime > datetime.utcnow(),
            models.Appointment.reminder_sent == False,
            models.Appointment.status.in_([models.AppointmentStatus.SCHEDULED, models.AppointmentStatus.CONFIRMED])
        )
    ).all()


def mark_reminder_sent(db: Session, appointment_id: int):
    appointment = db.query(models.Appointment).filter(
        models.Appointment.id == appointment_id
    ).first()
    if appointment:
        appointment.reminder_sent = True
        db.commit()
        db.refresh(appointment)
    return appointment