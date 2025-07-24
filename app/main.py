import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from .core.database import engine, Base
from .core.config import settings
from .api import auth, clients, services, appointments, dashboard
from .services.telegram_bot import telegram_bot
from .services.reminder_service import reminder_service

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events"""
    # Startup
    logger.info("Запуск приложения...")
    
    # Создаем таблицы базы данных
    Base.metadata.create_all(bind=engine)
    
    # Настраиваем и запускаем Telegram бота
    if settings.telegram_bot_token:
        try:
            telegram_bot.setup_bot()
            # Запускаем бота в фоновом режиме
            asyncio.create_task(telegram_bot.start_polling())
            logger.info("Telegram бот запущен")
        except Exception as e:
            logger.error(f"Ошибка запуска Telegram бота: {e}")
    
    # Запускаем сервис напоминаний
    try:
        reminder_service.start()
        logger.info("Сервис напоминаний запущен")
    except Exception as e:
        logger.error(f"Ошибка запуска сервиса напоминаний: {e}")
    
    yield
    
    # Shutdown
    logger.info("Остановка приложения...")
    reminder_service.stop()


app = FastAPI(
    title="CRM Система для малого бизнеса",
    description="Система управления клиентами с интеграцией Telegram бота",
    version="1.0.0",
    lifespan=lifespan
)

# Подключение статических файлов
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Настройка шаблонов
templates = Jinja2Templates(directory="app/templates")

# Подключение API роутеров
app.include_router(auth.router, prefix="/api/auth", tags=["Аутентификация"])
app.include_router(clients.router, prefix="/api/clients", tags=["Клиенты"])
app.include_router(services.router, prefix="/api/services", tags=["Услуги"])
app.include_router(appointments.router, prefix="/api/appointments", tags=["Записи"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Дашборд"])


# Веб-интерфейс
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Главная страница"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Страница входа"""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Страница регистрации"""
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Дашборд"""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/clients", response_class=HTMLResponse)
async def clients_page(request: Request):
    """Страница клиентов"""
    return templates.TemplateResponse("clients.html", {"request": request})


@app.get("/appointments", response_class=HTMLResponse)
async def appointments_page(request: Request):
    """Страница записей"""
    return templates.TemplateResponse("appointments.html", {"request": request})


@app.get("/services", response_class=HTMLResponse)
async def services_page(request: Request):
    """Страница услуг"""
    return templates.TemplateResponse("services.html", {"request": request})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)