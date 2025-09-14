FROM python:3.11-slim

WORKDIR /app

# Copy project files
COPY . /app

# Install system dependencies for Playwright + Python packages
RUN apt-get update && apt-get install -y \
	wget curl unzip fontconfig libnss3 libatk1.0-0 libcups2 \
	libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
	libpango1.0-0 libasound2 libxshmfence1 && \
	rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir fastapi uvicorn gunicorn crawl4ai python-dotenv playwright

# Install Playwright browsers
RUN playwright install --with-deps

# Expose port
EXPOSE 10000

# Start command (Gunicorn + Uvicorn workers)
CMD ["gunicorn", "app:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:10000"]
