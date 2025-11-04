FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY device_service /app/device_service
EXPOSE 8003
CMD ["uvicorn", "device_service.main:app", "--host", "0.0.0.0", "--port", "8003"]