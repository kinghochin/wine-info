# Use official Playwright Python image with browsers preinstalled
FROM mcr.microsoft.com/playwright/python:v1.44.0-focal

WORKDIR /app

# Copy your app
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir fastapi uvicorn crawl4ai python-dotenv

# Expose port
EXPOSE 10000

# Start FastAPI
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]
