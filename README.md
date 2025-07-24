# CRM Система для малого бизнеса

Современная CRM система с веб-интерфейсом и интеграцией Telegram бота для управления клиентами, записями и автоматическими напоминаниями.

## 🚀 Возможности

- **Управление клиентами**: Добавление, редактирование и удаление клиентов
- **Система записей**: Планирование и управление встречами/записями
- **Управление услугами**: Каталог предлагаемых услуг с ценами
- **Telegram бот**: Запись через бота и автоматические напоминания
- **Дашборд**: Статистика и аналитика
- **Аутентификация**: Безопасная система входа с JWT токенами
- **Адаптивный дизайн**: Современный веб-интерфейс

## 📋 Технологии

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: HTML, CSS, JavaScript (Vanilla)
- **Telegram**: python-telegram-bot
- **База данных**: PostgreSQL
- **Контейнеризация**: Docker, Docker Compose

## 🛠 Установка и запуск

### Через Docker (рекомендуется)

1. **Клонируйте репозиторий:**
```bash
git clone <repository-url>
cd crm-system
```

2. **Создайте файл .env:**
```bash
cp .env.example .env
```

3. **Настройте переменные окружения в .env:**
```env
DATABASE_URL=postgresql://crm_user:crm_password@postgres:5432/crm_db
TELEGRAM_BOT_TOKEN=your_bot_token_here
SECRET_KEY=your_secret_key_here_generate_with_openssl_rand_hex_32
DEBUG=False
TIMEZONE=Europe/Moscow
```

4. **Запустите систему:**
```bash
docker-compose up -d
```

5. **Инициализируйте базу данных:**
```bash
docker-compose exec app python init_db.py
```

### Ручная установка

1. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

2. **Настройте PostgreSQL:**
```bash
# Создайте базу данных и пользователя
sudo -u postgres psql
CREATE DATABASE crm_db;
CREATE USER crm_user WITH PASSWORD 'crm_password';
GRANT ALL PRIVILEGES ON DATABASE crm_db TO crm_user;
```

3. **Настройте .env файл и запустите:**
```bash
python init_db.py
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 🤖 Настройка Telegram бота

1. **Создайте бота через @BotFather в Telegram**
2. **Получите токен и добавьте его в .env файл**
3. **Перезапустите приложение**

### Команды бота:
- `/start` - Начать работу с ботом
- Интерактивные кнопки для записи и просмотра записей

## 📱 Использование

### Веб-интерфейс

1. **Откройте браузер и перейдите на** `http://localhost:8000`
2. **Войдите в систему:**
   - Email: `admin@example.com`
   - Пароль: `admin123`

### Основные функции:

- **Дашборд**: Просмотр статистики и последних записей
- **Клиенты**: Управление базой клиентов
- **Записи**: Планирование и отслеживание встреч
- **Услуги**: Управление каталогом услуг

### API

Документация API доступна по адресу: `http://localhost:8000/docs`

## 🔧 Конфигурация

### Переменные окружения:

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `DATABASE_URL` | URL подключения к PostgreSQL | - |
| `TELEGRAM_BOT_TOKEN` | Токен Telegram бота | - |
| `SECRET_KEY` | Секретный ключ для JWT | - |
| `DEBUG` | Режим отладки | `True` |
| `TIMEZONE` | Часовой пояс | `Europe/Moscow` |
| `REMINDER_HOURS_BEFORE` | За сколько часов напоминать | `24` |

### Генерация SECRET_KEY:
```bash
openssl rand -hex 32
```

## 📊 Структура проекта

```
crm-system/
├── app/
│   ├── api/              # API роутеры
│   ├── core/             # Конфигурация и база данных
│   ├── crud/             # CRUD операции
│   ├── models/           # Модели SQLAlchemy
│   ├── schemas/          # Pydantic схемы
│   ├── services/         # Бизнес-логика (Telegram, напоминания)
│   ├── static/           # Статические файлы (CSS, JS)
│   ├── templates/        # HTML шаблоны
│   └── main.py          # Главный файл приложения
├── docker-compose.yml    # Docker Compose конфигурация
├── Dockerfile           # Docker образ
├── requirements.txt     # Python зависимости
├── init_db.py          # Скрипт инициализации БД
└── README.md           # Документация
```

## 🔐 Безопасность

- JWT токены для аутентификации
- Хеширование паролей с bcrypt
- Валидация данных с Pydantic
- Разделение прав доступа (обычные пользователи/администраторы)

## 📝 API Endpoints

### Аутентификация
- `POST /api/auth/register` - Регистрация
- `POST /api/auth/login` - Вход
- `POST /api/auth/login-json` - Вход через JSON

### Клиенты
- `GET /api/clients` - Список клиентов
- `POST /api/clients` - Создать клиента
- `GET /api/clients/{id}` - Получить клиента
- `PUT /api/clients/{id}` - Обновить клиента
- `DELETE /api/clients/{id}` - Удалить клиента

### Записи
- `GET /api/appointments` - Список записей
- `POST /api/appointments` - Создать запись
- `GET /api/appointments/{id}` - Получить запись
- `PUT /api/appointments/{id}` - Обновить запись
- `DELETE /api/appointments/{id}` - Удалить запись

### Услуги
- `GET /api/services` - Список услуг
- `POST /api/services` - Создать услугу (только админ)
- `PUT /api/services/{id}` - Обновить услугу (только админ)

## 🚀 Развертывание в продакшене

1. **Используйте внешнюю базу данных PostgreSQL**
2. **Настройте HTTPS с помощью reverse proxy (nginx)**
3. **Установите DEBUG=False**
4. **Используйте сильный SECRET_KEY**
5. **Настройте резервное копирование базы данных**

### Пример nginx конфигурации:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🤝 Поддержка

Если у вас возникли вопросы или проблемы:

1. Проверьте логи: `docker-compose logs app`
2. Убедитесь, что все переменные окружения настроены
3. Проверьте подключение к базе данных

## 📄 Лицензия

Этот проект распространяется под лицензией MIT.

## 🔄 Обновления

Для получения обновлений:
```bash
git pull origin main
docker-compose down
docker-compose build
docker-compose up -d
```

---

**CRM Система** - Удобное решение для управления клиентской базой малого бизнеса! 🎯
