#!/bin/bash

set -e

echo "Ожидание подключения к базе данных..."

while ! python << END
import sys
import psycopg2
try:
    conn = psycopg2.connect(
        host="$DB_HOST",
        port="$DB_PORT",
        user="$DB_USER",
        password="$DB_PASSWORD",
        database="$DB_NAME"
    )
    conn.close()
    print("База данных готова!")
    sys.exit(0)
except Exception as e:
    print(f"Ошибка подключения к БД: {e}")
    sys.exit(1)
END
do
  echo "База данных недоступна — ожидание 2 секунды..."
  sleep 2
done

echo "Запуск миграций..."
python manage.py migrate --noinput

echo "Сборка статики..."
python manage.py collectstatic --noinput

exec "$@"