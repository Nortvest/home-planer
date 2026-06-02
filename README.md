# Домашний планёр

Две независимые части:

- **[backend/](backend/README.md)** — FastAPI-сервер, чистая архитектура, SQLite.
- **[frontend/](frontend/README.md)** — HTML/CSS/JS, без бандлеров и фреймворков.

Прочитайте соответствующий README для запуска.

## Быстрый старт

```bash
# Бэкенд
cd backend
uv sync --extra dev
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Фронтенд
cd frontend
python -m http.server 5500
```

Затем откройте `http://localhost:5500` в браузере.
