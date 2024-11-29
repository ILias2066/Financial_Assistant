# Используем официальный образ Python
FROM python:3.12-slim

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем файлы проекта в контейнер
COPY . /app

# Устанавливаем зависимости
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


# Открываем порт, если необходимо
EXPOSE 8000

# Команда для запуска приложения
CMD ["python", "main.py"]
