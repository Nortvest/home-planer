FROM python:3.13-slim

WORKDIR /app

# Install uv
RUN python -m ensurepip --upgrade && \
    python -m pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./

# Install dependencies into /app/.venv
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN uv sync --frozen

COPY src/ ./src/

RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
