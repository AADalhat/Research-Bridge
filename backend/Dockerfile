# Use official Python image based on your target version
FROM python:3.13-slim

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvbin/uv

WORKDIR /app

# Copy dependency definitions first for caching layers
COPY pyproject.toml uv.lock ./

# Install dependencies without virtual environment creation (system-wide inside container)
RUN /uvbin/uv sync --frozen --no-dev --no-editable

# Copy source code and configuration files
COPY . .

# Expose port and set run command
EXPOSE 8000
CMD ["/app/.venv/bin/uvicorn", "synaptix.main:app", "--host", "0.0.0.0", "--port", "8000"]