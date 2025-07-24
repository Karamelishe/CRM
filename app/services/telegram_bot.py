import logging
from datetime import datetime, timedelta
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, filters
)
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.database import SessionLocal
from ..crud import crud
from ..schemas import schemas
from ..models.models import AppointmentStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramBot:
    def __init__(self):
        self.application = None
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        user = update.effective_user
        
        # Сохраняем Telegram ID пользователя
        with SessionLocal() as db:
            # Ищем клиента по telegram username
            client = None
            if user.username:
                client = db.query(crud.models.Client).filter(
                    crud.models.Client.telegram_username == user.username
                ).first()
            
            if client:
                # Обновляем telegram_id если его не было
                if not client.telegram_id:
                    client.telegram_id = str(user.id)
                    db.commit()
                
                keyboard = [
                    [InlineKeyboardButton("📅 Записаться", callback_data="book_appointment")],
                    [InlineKeyboardButton("📋 Мои записи", callback_data="my_appointments")],
                    [InlineKeyboardButton("📞 Контакты", callback_data="contact_info")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"Привет, {client.full_name}! 👋\n\n"
                    "Я помогу вам управлять записями.\n"
                    "Выберите действие:",
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text(
                    "Добро пожаловать! 👋\n\n"
                    "Для работы с ботом вам необходимо быть зарегистрированным клиентом.\n"
                    "Обратитесь к администратору для регистрации."
                )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        user_id = str(query.from_user.id)
        
        with SessionLocal() as db:
            client = crud.get_client_by_telegram_id(db, user_id)
            
            if not client:
                await query.edit_message_text("Вы не зарегистрированы в системе.")
                return
            
            if query.data == "book_appointment":
                await self.show_services(query, db)
            elif query.data == "my_appointments":
                await self.show_my_appointments(query, db, client)
            elif query.data == "contact_info":
                await self.show_contact_info(query)
            elif query.data.startswith("book_service_"):
                service_id = int(query.data.split("_")[2])
                await self.book_service(query, db, client, service_id)
            elif query.data.startswith("cancel_appointment_"):
                appointment_id = int(query.data.split("_")[2])
                await self.cancel_appointment(query, db, client, appointment_id)
    
    async def show_services(self, query, db: Session):
        """Показать доступные услуги"""
        services = crud.get_services(db)
        
        if not services:
            await query.edit_message_text("На данный момент услуги недоступны.")
            return
        
        keyboard = []
        for service in services:
            price_text = f" - {service.price // 100} руб." if service.price else ""
            keyboard.append([
                InlineKeyboardButton(
                    f"{service.name} ({service.duration_minutes} мин){price_text}",
                    callback_data=f"book_service_{service.id}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "Выберите услугу для записи:",
            reply_markup=reply_markup
        )
    
    async def book_service(self, query, db: Session, client, service_id: int):
        """Записаться на услугу"""
        service = crud.get_service(db, service_id)
        
        if not service:
            await query.edit_message_text("Услуга не найдена.")
            return
        
        # Здесь можно добавить логику выбора времени
        # Для простоты создаем запись на завтра в 10:00
        tomorrow = datetime.now() + timedelta(days=1)
        appointment_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        
        appointment_data = schemas.AppointmentCreate(
            datetime=appointment_time,
            client_id=client.id,
            service_id=service_id,
            notes="Запись через Telegram бота"
        )
        
        appointment = crud.create_appointment(db, appointment_data, client.owner_id)
        
        await query.edit_message_text(
            f"✅ Вы успешно записаны!\n\n"
            f"Услуга: {service.name}\n"
            f"Дата: {appointment.datetime.strftime('%d.%m.%Y')}\n"
            f"Время: {appointment.datetime.strftime('%H:%M')}\n\n"
            f"Мы напомним вам о записи заранее."
        )
    
    async def show_my_appointments(self, query, db: Session, client):
        """Показать записи клиента"""
        now = datetime.now()
        appointments = db.query(crud.models.Appointment).filter(
            crud.models.Appointment.client_id == client.id,
            crud.models.Appointment.datetime > now,
            crud.models.Appointment.status.in_([
                AppointmentStatus.SCHEDULED, 
                AppointmentStatus.CONFIRMED
            ])
        ).order_by(crud.models.Appointment.datetime).all()
        
        if not appointments:
            await query.edit_message_text("У вас нет предстоящих записей.")
            return
        
        text = "📋 Ваши записи:\n\n"
        keyboard = []
        
        for appointment in appointments:
            service = crud.get_service(db, appointment.service_id)
            date_str = appointment.datetime.strftime('%d.%m.%Y %H:%M')
            status_emoji = "📅" if appointment.status == AppointmentStatus.SCHEDULED else "✅"
            
            text += f"{status_emoji} {service.name}\n"
            text += f"   📅 {date_str}\n"
            if appointment.notes:
                text += f"   📝 {appointment.notes}\n"
            text += "\n"
            
            keyboard.append([
                InlineKeyboardButton(
                    f"❌ Отменить {date_str}",
                    callback_data=f"cancel_appointment_{appointment.id}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)
    
    async def cancel_appointment(self, query, db: Session, client, appointment_id: int):
        """Отменить запись"""
        appointment = db.query(crud.models.Appointment).filter(
            crud.models.Appointment.id == appointment_id,
            crud.models.Appointment.client_id == client.id
        ).first()
        
        if not appointment:
            await query.edit_message_text("Запись не найдена.")
            return
        
        appointment.status = AppointmentStatus.CANCELLED
        db.commit()
        
        await query.edit_message_text(
            "❌ Запись отменена.\n\n"
            "Если хотите записаться на другое время, воспользуйтесь командой /start"
        )
    
    async def show_contact_info(self, query):
        """Показать контактную информацию"""
        await query.edit_message_text(
            "📞 Контактная информация:\n\n"
            "Телефон: +7 (XXX) XXX-XX-XX\n"
            "Email: info@example.com\n"
            "Адрес: г. Москва, ул. Примерная, 1\n\n"
            "Режим работы:\n"
            "Пн-Пт: 09:00 - 18:00\n"
            "Сб: 10:00 - 16:00\n"
            "Вс: выходной"
        )
    
    async def send_reminder(self, chat_id: str, appointment_text: str):
        """Отправить напоминание о записи"""
        if not self.application:
            return False
        
        try:
            await self.application.bot.send_message(
                chat_id=int(chat_id),
                text=f"🔔 Напоминание о записи!\n\n{appointment_text}"
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка отправки напоминания: {e}")
            return False
    
    def setup_bot(self):
        """Настройка бота"""
        if not settings.telegram_bot_token:
            logger.warning("Telegram bot token не установлен")
            return None
        
        self.application = Application.builder().token(settings.telegram_bot_token).build()
        
        # Добавляем обработчики
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        return self.application
    
    async def start_polling(self):
        """Запуск бота"""
        if self.application:
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()


# Глобальный экземпляр бота
telegram_bot = TelegramBot()