FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY shared /app/shared
COPY monitoring_service /app/monitoring_service
EXPOSE 8004
CMD ["uvicorn", "monitoring_service.main:app", "--host", "0.0.0.0", "--port", "8004"]