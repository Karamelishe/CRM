import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from ..core.database import SessionLocal
from ..core.config import settings
from ..crud import crud
from .telegram_bot import telegram_bot

logger = logging.getLogger(__name__)


class ReminderService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        
    async def check_and_send_reminders(self):
        """Проверить и отправить напоминания"""
        logger.info("Проверка напоминаний...")
        
        with SessionLocal() as db:
            # Получаем записи, для которых нужно отправить напоминания
            appointments = crud.get_appointments_needing_reminders(
                db, settings.reminder_hours_before
            )
            
            for appointment in appointments:
                if appointment.client.telegram_id:
                    # Формируем текст напоминания
                    service = crud.get_service(db, appointment.service_id)
                    date_str = appointment.datetime.strftime('%d.%m.%Y')
                    time_str = appointment.datetime.strftime('%H:%M')
                    
                    reminder_text = (
                        f"📅 Услуга: {service.name}\n"
                        f"📅 Дата: {date_str}\n"
                        f"🕐 Время: {time_str}\n\n"
                        f"💡 Если нужно отменить или перенести запись, "
                        f"обратитесь к администратору или воспользуйтесь ботом."
                    )
                    
                    # Отправляем напоминание
                    success = await telegram_bot.send_reminder(
                        appointment.client.telegram_id,
                        reminder_text
                    )
                    
                    if success:
                        # Отмечаем, что напоминание отправлено
                        crud.mark_reminder_sent(db, appointment.id)
                        logger.info(f"Напоминание отправлено для записи {appointment.id}")
                    else:
                        logger.error(f"Не удалось отправить напоминание для записи {appointment.id}")
                
                else:
                    logger.warning(f"У клиента {appointment.client.full_name} нет Telegram ID")
    
    def start(self):
        """Запуск планировщика"""
        # Проверяем напоминания каждые 30 минут
        self.scheduler.add_job(
            self.check_and_send_reminders,
            trigger=IntervalTrigger(minutes=30),
            id='reminder_check',
            name='Проверка напоминаний',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Сервис напоминаний запущен")
    
    def stop(self):
        """Остановка планировщика"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Сервис напоминаний остановлен")


# Глобальный экземпляр сервиса
reminder_service = ReminderService()