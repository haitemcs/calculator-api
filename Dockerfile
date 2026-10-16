# Start from a small official Python image.
FROM python:3.13-slim

# Keep container logs visible and avoid writing .pyc files into the image.
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

# Run the application as a non-root user inside the container.
RUN addgroup --system app && adduser --system --ingroup app app

# Copy dependency definitions first so Docker can cache the install layer.
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the application only after dependencies are installed.
COPY . .
RUN chown -R app:app /app
USER app

EXPOSE 8000

# Docker Compose overrides this command for the Celery worker service.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
