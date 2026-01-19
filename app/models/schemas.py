"""
Модуль для работы с Pydantic схемами и валидацией данных
"""

from pydantic import BaseModel
from typing import List, Optional


class FilmBase(BaseModel):
    """Базовая модель фильма"""
    film_id: int
    title: str
    description: Optional[str] = None
    release_year: int
    language_id: int


class FilmDetail(FilmBase):
    """Детальная модель фильма с дополнительной информацией"""
    length: Optional[int] = None
    rating: Optional[str] = None
    categories: Optional[List[str]] = None
    actors: Optional[List[str]] = None


class GenreResponse(BaseModel):
    """Модель ответа для жанра"""
    category_id: int
    name: str


class ActorResponse(BaseModel):
    """Модель ответа для актёра"""
    actor_id: int
    first_name: str
    last_name: str
    full_name: str


class SearchResponse(BaseModel):
    """Модель ответа для результатов поиска"""
    total_count: int
    page: int
    page_size: int
    films: List[FilmDetail]


class StatsResponse(BaseModel):
    """Модель ответа для статистики поисков"""
    search_type: str
    count: int
    params: dict


class YearRangeResponse(BaseModel):
    """Модель ответа для диапазона годов"""
    min_year: int
    max_year: int
