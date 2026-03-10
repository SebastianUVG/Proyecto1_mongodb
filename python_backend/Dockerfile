# Use full image so SSL/TLS to Atlas works (slim often fails with TLSV1_ALERT_INTERNAL_ERROR)
FROM python:3.11

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Ensure system CA certificates are installed for TLS (MongoDB Atlas)
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && \
    update-ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app /app/app

EXPOSE 8000

# MONGO_URI is required at runtime (Atlas)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
