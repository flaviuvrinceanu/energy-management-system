FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY load_balancer_service/ ./load_balancer_service/

WORKDIR /app/load_balancer_service

CMD ["python", "main.py"]
