# Подслушано Бот p12 (GitHub Deploy Version)

## Запуск локально:
pip install -r requirements.txt
создайте .env со значениями:
TOKEN=...
ADMIN_GROUP_ID=...
CHANNEL_ID=...

python bot.py

## Деплой:
Добавьте переменные окружения:
- TOKEN
- ADMIN_GROUP_ID
- CHANNEL_ID

Файл .env НЕ грузить в GitHub.
