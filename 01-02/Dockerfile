# Вказуємо базовий образ для Python
FROM python:3.12-slim

# Встановлюємо робочу директорію в контейнері
WORKDIR /app

# Копіюємо файли проекту в контейнер
COPY . /app

# Встановлюємо залежності
RUN pip install --no-cache-dir -r requirements.txt

# Команда для запуску вашої програми
CMD ["python", "code/main.py"]
