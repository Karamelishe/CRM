import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from .core.database import engine, Base
from .core.config import settings
from .api import auth
from .api import products, cart, orders

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

    yield
    
    # Shutdown
    logger.info("Остановка приложения...")


app = FastAPI(
    title="E-commerce Cyber Range Lab",
    description="Лабораторный интернет-магазин для отработки атак на бизнес-логику",
    version="1.0.0",
    lifespan=lifespan
)

# Подключение статических файлов
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Настройка шаблонов
templates = Jinja2Templates(directory="app/templates")

# Подключение API роутеров
app.include_router(auth.router, prefix="/api/auth", tags=["Аутентификация"])
app.include_router(products.router, prefix="/api/products", tags=["Товары"])
app.include_router(cart.router, prefix="/api/cart", tags=["Корзина"])
app.include_router(orders.router, prefix="/api/orders", tags=["Заказы"])


# Веб-интерфейс
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Главная страница каталога"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Страница входа"""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Страница регистрации"""
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/cart", response_class=HTMLResponse)
async def cart_page(request: Request):
    """Страница корзины"""
    return templates.TemplateResponse("cart.html", {"request": request})


@app.get("/account", response_class=HTMLResponse)
async def account_page(request: Request):
    """Заказы пользователя"""
    return templates.TemplateResponse("account.html", {"request": request})


@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """Административная панель"""
    return templates.TemplateResponse("admin.html", {"request": request})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
