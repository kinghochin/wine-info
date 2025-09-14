# Base image with Python + Playwright
FROM mcr.microsoft.com/playwright/python:v1.44.0-focal

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir fastapi uvicorn python-dotenv

# Install Playwright browsers
RUN playwright install

# Expose port
EXPOSE 10000

# Start the FastAPI app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]
