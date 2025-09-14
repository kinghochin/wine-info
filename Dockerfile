# Use official Playwright Python image (includes browsers and dependencies)
FROM mcr.microsoft.com/playwright/python:1.37.2-focal

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app
COPY . /app

# Install Playwright browsers (already mostly included, but safe to run)
RUN playwright install

# Expose port
EXPOSE 10000

# Start FastAPI
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]
