"""
API маршруты для поиска фильмов
"""

from fastapi import APIRouter, Query
import time
import logging
from typing import List, Optional

# Импорт локальных модулей
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from local_settings import dbconfig, MONGODB_URL_READ, MONGODB_URL_WRITE
from app.database.mysql_connector import MySQLConnector
from app.logging.log_writer import LogWriter
from app.logging.log_stats import LogStats
from app.models.schemas import FilmDetail, GenreResponse, ActorResponse, YearRangeResponse
from app.utils.formatter import format_film_response

# Настройка логирования
logger = logging.getLogger(__name__)

# Инициализация маршрутизатора
router = APIRouter(prefix="/api", tags=["films"])

# Инициализация подключений к БД (глобальные переменные)
mysql_db = MySQLConnector(dbconfig)
log_writer = LogWriter(MONGODB_URL_WRITE)
log_stats = LogStats(MONGODB_URL_READ)


# ===== ПОИСК ПО КЛЮЧЕВОМУ СЛОВУ =====
@router.get("/search/keyword")
async def search_by_keyword(
    q: str = Query(..., min_length=1, max_length=100, description="Ключевое слово"),
    page: int = Query(1, ge=1, description="Номер страницы")
):
    """
    Поиск фильмов по названию (ключевому слову)

    Query Parameters:
    - q: Ключевое слово для поиска
    - page: Номер страницы (по умолчанию 1)

    Returns:
    - total_count: Общее количество результатов
    - page: Текущая страница
    - page_size: Размер страницы
    - films: Список фильмов с информацией
    """
    start_time = time.time()

    try:
        # Выполнение поиска в БД
        films, total_count = mysql_db.search_by_keyword(q, page, page_size=10)

        # Обогащение данных (добавление актёров и жанров)
        enriched_films = []
        for film in films:
            actors = mysql_db.get_film_actors(film['film_id'])
            categories = mysql_db.get_film_categories(film['film_id'])
            enriched_films.append(format_film_response(film, actors, categories))

        execution_time = time.time() - start_time

        # Логирование запроса
        log_writer.log_search(
            search_type="keyword",
            params={"keyword": q},
            results_count=len(enriched_films),
            execution_time_ms=execution_time * 1000
        )

        return {
            "total_count": total_count,
            "page": page,
            "page_size": 10,
            "films": enriched_films
        }

    except Exception as e:
        logger.error(f"Ошибка при поиске по ключевому слову: {e}")
        return {
            "error": "Ошибка при поиске",
            "message": str(e)
        }


# ===== ПОИСК ПО ЖАНРУ И ГОДУ =====
@router.get("/search/genre-year")
async def search_by_genre_and_year(
    genre: str = Query(..., description="Название жанра"),
    year_from: int = Query(2000, ge=1895, le=2030, description="Год начала диапазона"),
    year_to: int = Query(2023, ge=1895, le=2030, description="Год конца диапазона"),
    page: int = Query(1, ge=1, description="Номер страницы")
):
    """
    Поиск фильмов по жанру и диапазону лет выпуска

    Query Parameters:
    - genre: Название жанра
    - year_from: Начало диапазона лет
    - year_to: Конец диапазона лет
    - page: Номер страницы

    Returns:
    - total_count: Общее количество результатов
    - page: Текущая страница
    - films: Список найденных фильмов
    """
    start_time = time.time()

    try:
        films, total_count = mysql_db.search_by_genre_and_year(
            genre, year_from, year_to, page, page_size=10
        )

        enriched_films = []
        for film in films:
            actors = mysql_db.get_film_actors(film['film_id'])
            categories = mysql_db.get_film_categories(film['film_id'])
            enriched_films.append(format_film_response(film, actors, categories))

        execution_time = time.time() - start_time

        log_writer.log_search(
            search_type="genre__years_range",
            params={
                "genre": genre,
                "years_range": f"{year_from}-{year_to}"
            },
            results_count=len(enriched_films),
            execution_time_ms=execution_time * 1000
        )

        return {
            "total_count": total_count,
            "page": page,
            "page_size": 10,
            "films": enriched_films
        }

    except Exception as e:
        logger.error(f"Ошибка при поиске по жанру и году: {e}")
        return {
            "error": "Ошибка при поиске",
            "message": str(e)
        }


# ===== ПОИСК ТОЛЬКО ПО ЖАНРУ =====
@router.get("/search/genre")
async def search_by_genre(
    genre: str = Query(..., description="Название жанра"),
    page: int = Query(1, ge=1, description="Номер страницы")
):
    """
    Поиск фильмов только по жанру

    Query Parameters:
    - genre: Название жанра
    - page: Номер страницы

    Returns:
    - total_count: Общее количество результатов
    - page: Текущая страница
    - films: Список найденных фильмов
    """
    start_time = time.time()

    try:
        films, total_count = mysql_db.search_by_genre(genre, page, page_size=10)

        enriched_films = []
        for film in films:
            actors = mysql_db.get_film_actors(film['film_id'])
            categories = mysql_db.get_film_categories(film['film_id'])
            enriched_films.append(format_film_response(film, actors, categories))

        execution_time = time.time() - start_time

        log_writer.log_search(
            search_type="genre",
            params={"genre": genre},
            results_count=len(enriched_films),
            execution_time_ms=execution_time * 1000
        )

        return {
            "total_count": total_count,
            "page": page,
            "page_size": 10,
            "films": enriched_films
        }

    except Exception as e:
        logger.error(f"Ошибка при поиске по жанру: {e}")
        return {
            "error": "Ошибка при поиске",
            "message": str(e)
        }


# ===== ПОИСК ПО АКТЁРУ =====
@router.get("/search/actor")
async def search_by_actor(
    actor_id: int = Query(..., ge=1, description="ID актёра"),
    page: int = Query(1, ge=1, description="Номер страницы")
):
    """
    Поиск фильмов по актёру

    Query Parameters:
    - actor_id: ID актёра
    - page: Номер страницы

    Returns:
    - total_count: Общее количество результатов
    - page: Текущая страница
    - films: Список фильмов с участием актёра
    """
    start_time = time.time()

    try:
        films, total_count = mysql_db.search_by_actor(actor_id, page, page_size=10)

        enriched_films = []
        for film in films:
            actors = mysql_db.get_film_actors(film['film_id'])
            categories = mysql_db.get_film_categories(film['film_id'])
            enriched_films.append(format_film_response(film, actors, categories))

        execution_time = time.time() - start_time

        # Получаем имя актёра для логирования
        actor_info = mysql_db.get_actor_by_id(actor_id)
        actor_name = f"{actor_info['first_name']} {actor_info['last_name']}" if actor_info else f"ID: {actor_id}"
        
        log_writer.log_search(
            search_type="actor",
            params={"actor_name": actor_name},
            results_count=len(enriched_films),
            execution_time_ms=execution_time * 1000
        )

        return {
            "total_count": total_count,
            "page": page,
            "page_size": 10,
            "films": enriched_films
        }

    except Exception as e:
        logger.error(f"Ошибка при поиске по актёру: {e}")
        return {
            "error": "Ошибка при поиске",
            "message": str(e)
        }


# ===== ПОЛУЧЕНИЕ ЖАНРОВ =====
@router.get("/genres", response_model=List[GenreResponse])
async def get_genres():
    """
    Получение списка всех доступных жанров

    Returns:
    - List[GenreResponse]: Список жанров с ID и названием
    """
    try:
        genres = mysql_db.get_all_genres()
        return [
            GenreResponse(category_id=g['category_id'], name=g['name'])
            for g in genres
        ]
    except Exception as e:
        logger.error(f"Ошибка при получении жанров: {e}")
        return []


# ===== ПОЛУЧЕНИЕ АКТЁРОВ =====
@router.get("/actors", response_model=List[ActorResponse])
async def get_actors():
    """
    Получение списка всех доступных актёров

    Returns:
    - List[ActorResponse]: Список актёров с ID и полным именем
    """
    try:
        actors = mysql_db.get_all_actors()
        return [
            ActorResponse(
                actor_id=a['actor_id'],
                first_name=a['first_name'],
                last_name=a['last_name'],
                full_name=f"{a['first_name']} {a['last_name']}"
            )
            for a in actors
        ]
    except Exception as e:
        logger.error(f"Ошибка при получении актёров: {e}")
        return []


# ===== ПОЛУЧЕНИЕ ДИАПАЗОНА ЛЕТ =====
@router.get("/year-range", response_model=YearRangeResponse)
async def get_year_range():
    """
    Получение диапазона лет для фильмов в БД

    Returns:
    - YearRangeResponse: Минимальный и максимальный год
    """
    try:
        year_range = mysql_db.get_year_range()
        return YearRangeResponse(
            min_year=year_range['min_year'],
            max_year=year_range['max_year']
        )
    except Exception as e:
        logger.error(f"Ошибка при получении диапазона лет: {e}")
        return {"min_year": 1990, "max_year": 2025}


# ===== ПОЛУЧЕНИЕ ДИАПАЗОНА ЛЕТ ДЛЯ ЖАНРА =====
@router.get("/year-range-for-genre", response_model=YearRangeResponse)
async def get_year_range_for_genre(genre: str = Query(..., description="Название жанра")):
    """
    Получение диапазона лет для конкретного жанра

    Query Parameters:
    - genre: Название жанра

    Returns:
    - YearRangeResponse: Минимальный и максимальный год для жанра
    """
    try:
        year_range = mysql_db.get_year_range_for_genre(genre)
        return YearRangeResponse(
            min_year=year_range['min_year'],
            max_year=year_range['max_year']
        )
    except Exception as e:
        logger.error(f"Ошибка при получении диапазона лет для жанра: {e}")
        return {"min_year": 1990, "max_year": 2025}


# ===== ПОЛУЧЕНИЕ СТАТИСТИКИ - ПОПУЛЯРНЫЕ ЗАПРОСЫ =====
@router.get("/stats/popular")
async def get_popular_stats():
    """
    Получение топ 5 популярных поисков

    Returns:
    - List[Dict]: Список популярных запросов с указанием типа и количества
    """
    try:
        popular = log_stats.get_popular_searches(limit=5)
        return {
            "popular_searches": popular
        }
    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}")
        return {"popular_searches": []}


# ===== ПОЛУЧЕНИЕ СТАТИСТИКИ - ПОСЛЕДНИЕ ЗАПРОСЫ =====
@router.get("/stats/recent")
async def get_recent_stats():
    """
    Получение последних 5 уникальных поисков

    Returns:
    - List[Dict]: Список последних поисков с временем выполнения
    """
    try:
        recent = log_stats.get_recent_searches(limit=5)
        return {
            "recent_searches": recent
        }
    except Exception as e:
        logger.error(f"Ошибка при получении последних поисков: {e}")
        return {"recent_searches": []}
