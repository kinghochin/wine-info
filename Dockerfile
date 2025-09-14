# Use official Python image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies required by Playwright and browsers
RUN apt-get update && apt-get install -y \
	curl wget gnupg ca-certificates \
	fonts-liberation libnss3 libatk1.0-0 libcups2 \
	libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
	libpango1.0-0 libasound2 libxshmfence1 libwayland-client0 \
	libwayland-cursor0 libx11-xcb1 libxcb1 libxcomposite1 libxext6 \
	libxi6 libxrender1 libxrandr2 libxtst6 libglib2.0-0 -y \
	&& rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app
COPY . /app

# Install Playwright browsers
RUN python -m playwright install

# Expose port
EXPOSE 10000

# Start FastAPI
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]
