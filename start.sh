#!/bin/bash

# Скрипт быстрого запуска CRM системы

echo "🚀 Запуск CRM системы..."

# Проверяем наличие Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker для продолжения."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Установите Docker Compose для продолжения."
    exit 1
fi

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "⚠️  Файл .env не найден. Создаю из примера..."
    cp .env.example .env
    echo "✅ Файл .env создан. Пожалуйста, настройте переменные окружения:"
    echo "   - SECRET_KEY (сгенерируйте командой: openssl rand -hex 32)"
    echo ""
    echo "После настройки запустите скрипт снова."
    exit 1
fi

# Запускаем контейнеры
echo "🐳 Запуск Docker контейнеров..."
docker-compose up -d

# Ждем запуска базы данных
echo "⏳ Ожидание запуска базы данных..."
sleep 10

# Инициализируем базу данных
echo "🗄️  Инициализация базы данных..."
docker-compose exec -T app python init_db.py

echo ""
echo "🎉 CRM система запущена!"
echo ""
echo "📱 Веб-интерфейс: http://localhost:8000"
echo "📖 API документация: http://localhost:8000/docs"
echo ""
echo "🔑 Данные для входа:"
echo "   Email: admin@example.com"
echo "   Пароль: admin123"
echo ""
echo "📊 Проверить статус: docker-compose ps"
echo "📝 Просмотр логов: docker-compose logs -f"
echo "⏹️  Остановка: docker-compose down"
echo ""
