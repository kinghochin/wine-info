# 1. Base image with Python and Playwright deps
FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

# 2. Install uv (fast Python package manager)
RUN pip install uv

# 3. Set working directory
WORKDIR /app

# 4. Copy dependency files
COPY pyproject.toml uv.lock* ./

# 5. Install dependencies with uv
RUN uv sync --frozen --no-dev

# 6. Copy app source code
COPY . .

# 7. Ensure Playwright browsers are installed
RUN playwright install --with-deps chromium

# 8. Expose Render port
EXPOSE 10000

# 9. Start FastAPI with uvicorn
CMD ["uv", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]
