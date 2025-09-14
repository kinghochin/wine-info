FROM python:3.11-slim

WORKDIR /app

# Copy your app files
COPY . /app

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
	wget curl gnupg ca-certificates \
	fonts-liberation libnss3 libatk1.0-0 libcups2 \
	libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
	libpango1.0-0 libasound2 libxshmfence1 libwayland-client0 \
	libwayland-cursor0 libx11-xcb1 libxcb1 libxcomposite1 libxext6 \
	libxi6 libxrender1 libxrandr2 libxtst6 libglib2.0-0 -y \
	&& rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir fastapi uvicorn crawl4ai python-dotenv playwright

# Install Playwright browsers
RUN playwright install --with-deps

# Expose port
EXPOSE 10000

# Start the FastAPI app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]
