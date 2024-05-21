# Используем базовый образ с Python
FROM python:3.9-slim

# Устанавливаем переменную окружения для Python
ENV PYTHONUNBUFFERED 1

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем зависимости проекта в контейнер
COPY requirements.txt /app/

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все остальные файлы в контейнер
COPY . /app/

# Команда для запуска приложения
CMD ["python", "app.py"]