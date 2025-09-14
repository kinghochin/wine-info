# Base image
FROM python:3.11-slim

# Set environment
ENV PYTHONUNBUFFERED=1
ENV PORT=10000

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
	libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxkbcommon0 \
	libxcomposite1 libxdamage1 libxrandr2 libgbm1 libpango1.0-0 \
	libasound2 libxshmfence1 wget curl unzip fontconfig git \
	&& rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python dependencies
COPY pyproject.toml poetry.lock* /app/

# Install Poetry
RUN pip install --no-cache-dir poetry

# Install dependencies without virtualenv
RUN poetry config virtualenvs.create false \
	&& poetry install --no-interaction --no-ansi --only main

# Copy app code
COPY . /app

# Install Playwright and browsers
RUN pip install --no-cache-dir playwright gunicorn \
	&& playwright install --with-deps

# Expose port
EXPOSE 10000

# Start the FastAPI app
CMD ["gunicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]
