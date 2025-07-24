# Руководство по установке CRM системы

## 🚀 Быстрый запуск

### Автоматический запуск
```bash
./start.sh
```

### Ручной запуск

1. **Подготовка окружения:**
```bash
cp .env.example .env
# Отредактируйте .env файл (см. раздел "Конфигурация")
```

2. **Запуск через Docker:**
```bash
docker-compose up -d
docker-compose exec app python init_db.py
```

3. **Запуск без Docker:**
```bash
# Установка зависимостей
pip install -r requirements.txt

# Настройка PostgreSQL (см. раздел "База данных")

# Инициализация и запуск
python init_db.py
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 🔧 Конфигурация

### Обязательные настройки в .env:

```env
# База данных
DATABASE_URL=postgresql://crm_user:crm_password@localhost:5432/crm_db

# Секретный ключ (сгенерируйте: openssl rand -hex 32)
SECRET_KEY=ваш_секретный_ключ_здесь

# Telegram бот (опционально)
TELEGRAM_BOT_TOKEN=токен_от_botfather

# Общие настройки
DEBUG=False
TIMEZONE=Europe/Moscow
```

### Генерация SECRET_KEY:
```bash
openssl rand -hex 32
```

## 🗄️ База данных

### Через Docker (рекомендуется)
База данных PostgreSQL автоматически настраивается при запуске docker-compose.

### Ручная настройка PostgreSQL:

1. **Установка PostgreSQL:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# CentOS/RHEL
sudo yum install postgresql-server postgresql-contrib
sudo postgresql-setup initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

2. **Создание базы данных:**
```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE crm_db;
CREATE USER crm_user WITH PASSWORD 'crm_password';
GRANT ALL PRIVILEGES ON DATABASE crm_db TO crm_user;
\q
```

3. **Настройка подключения:**
Отредактируйте файл `/etc/postgresql/*/main/pg_hba.conf`:
```
# Добавьте строку:
local   crm_db    crm_user    md5
```

## 🤖 Настройка Telegram бота

### 1. Создание бота:
1. Найдите @BotFather в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Получите токен бота

### 2. Настройка:
Добавьте токен в .env файл:
```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 3. Настройка команд бота:
Отправьте @BotFather команду `/setcommands` и добавьте:
```
start - Начать работу с ботом
```

## 🔐 Первый запуск

### 1. Инициализация базы данных:
```bash
python init_db.py
```

### 2. Данные для входа:
- **Email:** admin@example.com
- **Пароль:** admin123

### 3. Веб-интерфейс:
Откройте браузер и перейдите на `http://localhost:8000`

## 📦 Развертывание в продакшене

### 1. Reverse Proxy (nginx):

Создайте файл `/etc/nginx/sites-available/crm`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/crm/app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 2. SSL сертификат (Let's Encrypt):
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 3. Systemd сервис:

Создайте файл `/etc/systemd/system/crm.service`:
```ini
[Unit]
Description=CRM System
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/path/to/crm
Environment=PATH=/path/to/crm/venv/bin
ExecStart=/path/to/crm/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Запуск сервиса:
```bash
sudo systemctl daemon-reload
sudo systemctl enable crm
sudo systemctl start crm
```

### 4. Настройки безопасности:
```env
DEBUG=False
SECRET_KEY=очень_сложный_секретный_ключ
```

## 🔧 Обслуживание

### Резервное копирование базы данных:
```bash
# Создание бэкапа
docker-compose exec postgres pg_dump -U crm_user crm_db > backup.sql

# Восстановление из бэкапа
docker-compose exec -T postgres psql -U crm_user crm_db < backup.sql
```

### Просмотр логов:
```bash
# Docker логи
docker-compose logs -f app

# Системные логи
sudo journalctl -u crm -f
```

### Обновление системы:
```bash
git pull origin main
docker-compose down
docker-compose build
docker-compose up -d
```

## ❗ Устранение неполадок

### 1. Ошибка подключения к базе данных:
- Проверьте правильность DATABASE_URL в .env
- Убедитесь, что PostgreSQL запущен
- Проверьте права доступа пользователя к базе данных

### 2. Telegram бот не отвечает:
- Проверьте правильность TELEGRAM_BOT_TOKEN
- Убедитесь, что токен активен в @BotFather
- Проверьте логи приложения

### 3. Ошибки в веб-интерфейсе:
- Проверьте браузерную консоль (F12)
- Убедитесь, что статические файлы доступны
- Проверьте настройки CORS, если используете отдельный домен

### 4. Проблемы с правами доступа:
```bash
# Проверьте владельца файлов
sudo chown -R www-data:www-data /path/to/crm

# Установите правильные права
sudo chmod -R 755 /path/to/crm
```

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи: `docker-compose logs app`
2. Убедитесь в корректности .env файла
3. Проверьте статус сервисов: `docker-compose ps`
4. Попробуйте перезапустить: `docker-compose restart`

## 🔄 Дополнительные команды

### Сброс базы данных:
```bash
docker-compose down -v
docker-compose up -d
docker-compose exec app python init_db.py
```

### Создание суперпользователя:
```python
# Через Django shell или создайте скрипт
from app.crud import crud
from app.schemas import schemas
from app.core.database import SessionLocal

db = SessionLocal()
user = crud.create_user(db, schemas.UserCreate(
    email="your@email.com",
    password="your_password",
    full_name="Your Name"
))
user.is_admin = True
db.commit()
```

---

**Успешной установки! 🎉**