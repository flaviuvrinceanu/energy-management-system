FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY customer_support_service/ ./customer_support_service/

WORKDIR /app/customer_support_service

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]
