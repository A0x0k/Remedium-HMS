FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# مهم جدًا: المكتبات دي لازم تكون موجودة قبل pip install
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

COPY . .

RUN mkdir -p logs staticfiles media

RUN SECRET_KEY=build-only-secret-key-for-static-collection-not-for-runtime \
    python manage.py collectstatic --noinput

RUN adduser --disabled-password --no-create-home appuser \
    && chown -R appuser:appuser /app \
    && chmod -R 755 /app
USER appuser

EXPOSE 8000

CMD ["sh", "-c", "gunicorn remedium_hms.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${GUNICORN_WORKERS:-4}"]