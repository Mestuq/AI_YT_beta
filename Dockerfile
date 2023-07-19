FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .

RUN apt-get update && \
    apt-get install -y ffmpeg && \
    pip install --no-cache-dir -r requirements.txt

COPY www www

EXPOSE 5000
ENV PYTHONUNBUFFERED=1
CMD ["python", "www/main.py"]
