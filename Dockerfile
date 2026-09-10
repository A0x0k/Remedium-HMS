FROM python:3.13-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set work directory
WORKDIR /app

# Install system dependencies (including what psycopg2-binary needs)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy project
COPY . .

# Create necessary directories
RUN mkdir -p logs staticfiles media

# Collect static files
RUN SECRET_KEY=build-only-secret-key-for-static-collection-not-for-runtime \
    python manage.py collectstatic --noinput

# Create non-root user and set permissions
RUN adduser --disabled-password --no-create-home appuser \
    && chown -R appuser:appuser /app \
    && chmod -R 755 /app
USER appuser

# Expose port
EXPOSE 8000

# Run gunicorn (using $PORT for Railway compatibility)
CMD ["sh", "-c", "gunicorn remedium_hms.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${GUNICORN_WORKERS:-4}"]