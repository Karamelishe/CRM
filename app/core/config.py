from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Настройки базы данных
    database_url: str = "postgresql://crm_user:crm_password@localhost:5432/crm_db"
    
    # Telegram настройки
    telegram_bot_token: Optional[str] = None
    
    # Безопасность
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Общие настройки
    debug: bool = True
    timezone: str = "Europe/Moscow"
    
    # Настройки напоминаний
    reminder_hours_before: int = 24  # За сколько часов напоминать
    
    class Config:
        env_file = ".env"


settings = Settings()