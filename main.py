"""
Film Search Project - FastAPI Web Application
Главный модуль приложения
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

from app.routes import films

# Инициализация FastAPI приложения
app = FastAPI(
    title="Film Search API",
    description="API для поиска фильмов из базы данных Sakila",
    version="1.0.0"
)

# Подключение CORS для кросс-доменных запросов
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение статических файлов (CSS, JS, изображения)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключение маршрутов
app.include_router(films.router)


@app.get("/")
async def root():
    """Главная страница приложения"""
    return FileResponse("static/index.html")


@app.get("/health")
async def health_check():
    """Проверка здоровья приложения"""
    return {"status": "ok"}


if __name__ == "__main__":
    # Запуск сервера Uvicorn на localhost:8000
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
