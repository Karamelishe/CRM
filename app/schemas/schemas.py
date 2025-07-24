from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from ..models.models import AppointmentStatus


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class User(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Client schemas
class ClientBase(BaseModel):
    full_name: str
    phone: str
    email: Optional[str] = None
    telegram_username: Optional[str] = None
    notes: Optional[str] = None


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    telegram_username: Optional[str] = None
    notes: Optional[str] = None


class Client(ClientBase):
    id: int
    telegram_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Service schemas
class ServiceBase(BaseModel):
    name: str
    description: Optional[str] = None
    duration_minutes: int = 60
    price: Optional[int] = None


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    price: Optional[int] = None
    is_active: Optional[bool] = None


class Service(ServiceBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Appointment schemas
class AppointmentBase(BaseModel):
    datetime: datetime
    notes: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    client_id: int
    service_id: int


class AppointmentUpdate(BaseModel):
    datetime: Optional[datetime] = None
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None


class Appointment(AppointmentBase):
    id: int
    status: AppointmentStatus
    reminder_sent: bool
    created_at: datetime
    updated_at: datetime
    client: Client
    service: Service

    class Config:
        from_attributes = True


# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


# Telegram schemas
class TelegramMessage(BaseModel):
    text: str
    chat_id: int


# Dashboard schemas
class DashboardStats(BaseModel):
    total_clients: int
    total_appointments: int
    today_appointments: int
    upcoming_appointments: int