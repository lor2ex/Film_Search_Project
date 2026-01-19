"""
DAO (Data Access Object) для работы с MySQL базой данных Sakila
Класс обрабатывает все операции с базой данных и включает обработку ошибок
"""

import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Tuple, Optional
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MySQLConnector:
    """
    Data Access Object для работы с базой данных MySQL.
    Обеспечивает безопасное подключение и выполнение запросов.
    """

    def __init__(self, config: dict):
        """
        Инициализация подключения к базе данных

        Args:
            config (dict): Словарь конфигурации с параметрами подключения
                          (host, user, password, database)
        """
        self.config = config
        self.connection = None
        self._connect()

    def _connect(self) -> bool:
        """
        Установка подключения к базе данных с обработкой ошибок

        Returns:
            bool: True если подключение успешно, False в противном случае
        """
        try:
            self.connection = mysql.connector.connect(**self.config)
            if self.connection.is_connected():
                logger.info(f"Подключение к БД успешно: {self.config['database']}")
                return True
        except Error as err:
            if err.errno == 2003:
                logger.error("Ошибка подключения: сервер недоступен")
            elif err.errno == 1045:
                logger.error("Ошибка подключения: неверные учётные данные")
            else:
                logger.error(f"Ошибка подключения: {err}")
            return False

    def close(self) -> None:
        """Закрытие подключения к базе данных"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Подключение к БД закрыто")

    def _execute_query(self, query: str, params: Tuple = None) -> Optional[List[Dict]]:
        """
        Выполнение SELECT запроса с обработкой ошибок

        Args:
            query (str): SQL запрос
            params (Tuple): Параметры для защиты от SQL injection

        Returns:
            List[Dict]: Список словарей с результатами или None при ошибке
        """
        try:
            cursor = self.connection.cursor(dictionary=True)
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            result = cursor.fetchall()
            cursor.close()
            return result
        except Error as err:
            logger.error(f"Ошибка при выполнении запроса: {err}")
            return None

    # ===== ПОИСК ПО КЛЮЧЕВОМУ СЛОВУ =====
    def search_by_keyword(self, keyword: str, page: int = 1, page_size: int = 10) -> Tuple[List[Dict], int]:
        """
        Поиск фильмов по названию (ключевому слову)

        Args:
            keyword (str): Ключевое слово для поиска
            page (int): Номер страницы
            page_size (int): Количество результатов на странице

        Returns:
            Tuple[List[Dict], int]: Кортеж (список фильмов, общее количество)
        """
        offset = (page - 1) * page_size

        # Получение общего количества результатов
        count_query = "SELECT COUNT(*) as total FROM film WHERE title LIKE %s"
        count_result = self._execute_query(count_query, (f"%{keyword}%",))
        total_count = count_result[0]['total'] if count_result else 0

        # Получение фильмов с постраничной навигацией
        query = """
            SELECT f.film_id, f.title, f.description, f.release_year, 
                   f.length, f.rating, f.language_id
            FROM film f
            WHERE f.title LIKE %s
            ORDER BY f.release_year DESC
            LIMIT %s OFFSET %s
        """
        films = self._execute_query(query, (f"%{keyword}%", page_size, offset))
        return films or [], total_count

    # ===== ПОИСК ПО ЖАНРУ И ГОДУ =====
    def search_by_genre_and_year(
        self,
        genre: str,
        year_from: int,
        year_to: int,
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List[Dict], int]:
        """
        Поиск фильмов по жанру и диапазону лет выпуска

        Args:
            genre (str): Название жанра
            year_from (int): Год начала диапазона
            year_to (int): Год конца диапазона
            page (int): Номер страницы
            page_size (int): Количество результатов на странице

        Returns:
            Tuple[List[Dict], int]: Кортеж (список фильмов, общее количество)
        """
        offset = (page - 1) * page_size

        # Получение общего количества результатов
        count_query = """
            SELECT COUNT(DISTINCT f.film_id) as total
            FROM film f
            JOIN film_category fc ON f.film_id = fc.film_id
            JOIN category c ON fc.category_id = c.category_id
            WHERE c.name = %s AND f.release_year BETWEEN %s AND %s
        """
        count_result = self._execute_query(count_query, (genre, year_from, year_to))
        total_count = count_result[0]['total'] if count_result else 0

        # Получение фильмов
        query = """
            SELECT DISTINCT f.film_id, f.title, f.description, f.release_year,
                   f.length, f.rating, f.language_id
            FROM film f
            JOIN film_category fc ON f.film_id = fc.film_id
            JOIN category c ON fc.category_id = c.category_id
            WHERE c.name = %s AND f.release_year BETWEEN %s AND %s
            ORDER BY f.release_year DESC
            LIMIT %s OFFSET %s
        """
        films = self._execute_query(
            query,
            (genre, year_from, year_to, page_size, offset)
        )
        return films or [], total_count

    # ===== ПОИСК ТОЛЬКО ПО ЖАНРУ =====
    def search_by_genre(
        self,
        genre: str,
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List[Dict], int]:
        """
        Поиск фильмов только по жанру

        Args:
            genre (str): Название жанра
            page (int): Номер страницы
            page_size (int): Количество результатов на странице

        Returns:
            Tuple[List[Dict], int]: Кортеж (список фильмов, общее количество)
        """
        offset = (page - 1) * page_size

        # Получение общего количества результатов
        count_query = """
            SELECT COUNT(DISTINCT f.film_id) as total
            FROM film f
            JOIN film_category fc ON f.film_id = fc.film_id
            JOIN category c ON fc.category_id = c.category_id
            WHERE c.name = %s
        """
        count_result = self._execute_query(count_query, (genre,))
        total_count = count_result[0]['total'] if count_result else 0

        # Получение фильмов
        query = """
            SELECT DISTINCT f.film_id, f.title, f.description, f.release_year,
                   f.length, f.rating, f.language_id
            FROM film f
            JOIN film_category fc ON f.film_id = fc.film_id
            JOIN category c ON fc.category_id = c.category_id
            WHERE c.name = %s
            ORDER BY f.release_year DESC
            LIMIT %s OFFSET %s
        """
        films = self._execute_query(query, (genre, page_size, offset))
        return films or [], total_count

    # ===== ПОЛУЧЕНИЕ ДИАПАЗОНА ЛЕТ ДЛЯ ЖАНРА =====
    def get_year_range_for_genre(self, genre: str) -> Dict[str, int]:
        """
        Получение диапазона лет для конкретного жанра

        Args:
            genre (str): Название жанра

        Returns:
            Dict[str, int]: Словарь с минимальным и максимальным годом для жанра
        """
        query = """
            SELECT MIN(f.release_year) as min_year, MAX(f.release_year) as max_year
            FROM film f
            JOIN film_category fc ON f.film_id = fc.film_id
            JOIN category c ON fc.category_id = c.category_id
            WHERE c.name = %s
        """
        result = self._execute_query(query, (genre,))
        if result and result[0]['min_year'] is not None:
            return {
                'min_year': result[0]['min_year'],
                'max_year': result[0]['max_year']
            }
        return {'min_year': 2000, 'max_year': 2010}

    # ===== ПОИСК ПО АКТЁРУ =====
    def search_by_actor(
        self,
        actor_id: int,
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List[Dict], int]:
        """
        Поиск фильмов по актёру

        Args:
            actor_id (int): ID актёра
            page (int): Номер страницы
            page_size (int): Количество результатов на странице

        Returns:
            Tuple[List[Dict], int]: Кортеж (список фильмов, общее количество)
        """
        offset = (page - 1) * page_size

        # Получение общего количества результатов
        count_query = """
            SELECT COUNT(DISTINCT f.film_id) as total
            FROM film f
            JOIN film_actor fa ON f.film_id = fa.film_id
            WHERE fa.actor_id = %s
        """
        count_result = self._execute_query(count_query, (actor_id,))
        total_count = count_result[0]['total'] if count_result else 0

        # Получение фильмов
        query = """
            SELECT DISTINCT f.film_id, f.title, f.description, f.release_year,
                   f.length, f.rating, f.language_id
            FROM film f
            JOIN film_actor fa ON f.film_id = fa.film_id
            WHERE fa.actor_id = %s
            ORDER BY f.release_year DESC
            LIMIT %s OFFSET %s
        """
        films = self._execute_query(query, (actor_id, page_size, offset))
        return films or [], total_count

    # ===== ПОЛУЧЕНИЕ ЖАНРОВ =====
    def get_all_genres(self) -> List[Dict]:
        """
        Получение списка всех жанров из базы данных

        Returns:
            List[Dict]: Список словарей с жанрами (id, name)
        """
        query = "SELECT category_id, name FROM category ORDER BY name"
        genres = self._execute_query(query)
        return genres or []

    # ===== ПОЛУЧЕНИЕ АКТЁРОВ =====
    def get_all_actors(self) -> List[Dict]:
        """
        Получение списка всех актёров из базы данных

        Returns:
            List[Dict]: Список словарей с актёрами (actor_id, first_name, last_name)
        """
        query = """
            SELECT actor_id, first_name, last_name
            FROM actor
            ORDER BY first_name, last_name
            LIMIT 100
        """
        actors = self._execute_query(query)
        return actors or []

    # ===== ПОЛУЧЕНИЕ ДИАПАЗОНА ЛЕТ =====
    def get_year_range(self) -> Dict[str, int]:
        """
        Получение диапазона лет для фильмов в базе данных

        Returns:
            Dict[str, int]: Словарь с минимальным и максимальным годом
        """
        query = """
            SELECT MIN(release_year) as min_year, MAX(release_year) as max_year
            FROM film
        """
        result = self._execute_query(query)
        if result:
            return {
                'min_year': result[0]['min_year'],
                'max_year': result[0]['max_year']
            }
        return {'min_year': 2000, 'max_year': 2010}

    # ===== ДОПОЛНИТЕЛЬНЫЕ МЕТОДЫ =====
    def get_film_details(self, film_id: int) -> Optional[Dict]:
        """
        Получение полной информации о фильме

        Args:
            film_id (int): ID фильма

        Returns:
            Optional[Dict]: Словарь с информацией о фильме или None
        """
        query = """
            SELECT f.film_id, f.title, f.description, f.release_year,
                   f.length, f.rating
            FROM film f
            WHERE f.film_id = %s
        """
        result = self._execute_query(query, (film_id,))
        return result[0] if result else None

    def get_film_actors(self, film_id: int) -> List[str]:
        """
        Получение списка актёров для фильма

        Args:
            film_id (int): ID фильма

        Returns:
            List[str]: Список имён актёров
        """
        query = """
            SELECT CONCAT(a.first_name, ' ', a.last_name) as actor_name
            FROM actor a
            JOIN film_actor fa ON a.actor_id = fa.actor_id
            WHERE fa.film_id = %s
        """
        result = self._execute_query(query, (film_id,))
        return [row['actor_name'] for row in result] if result else []

    def get_film_categories(self, film_id: int) -> List[str]:
        """
        Получение списка жанров для фильма

        Args:
            film_id (int): ID фильма

        Returns:
            List[str]: Список названий жанров
        """
        query = """
            SELECT c.name
            FROM category c
            JOIN film_category fc ON c.category_id = fc.category_id
            WHERE fc.film_id = %s
        """
        result = self._execute_query(query, (film_id,))
        return [row['name'] for row in result] if result else []

    def get_actor_by_id(self, actor_id: int) -> Optional[Dict]:
        """
        Получение информации об актёре по ID

        Args:
            actor_id (int): ID актёра

        Returns:
            Optional[Dict]: Словарь с информацией об актёре или None
        """
        query = """
            SELECT actor_id, first_name, last_name
            FROM actor
            WHERE actor_id = %s
        """
        result = self._execute_query(query, (actor_id,))
        return result[0] if result else None
