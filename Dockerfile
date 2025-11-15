FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# XÓA BỎ CÁC LỆNH RUN mkdir/chmod
# Chúng không còn cần thiết

ENV FLASK_APP=app.py

EXPOSE 8080

# Sửa: Dùng wsgi:app để chạy file wsgi.py (tốt hơn cho production)
# SỬA LẠI THÀNH:
# SỬA LẠI THÀNH:
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app", "--log-level", "debug"]