"""
Модуль для получения статистики поисков из MongoDB
"""

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class LogStats:
    """
    Класс для получения статистики поисковых запросов из MongoDB
    """

    def __init__(self, mongodb_url: str, database_name: str = 'ich_edit'):
        """
        Инициализация подключения к MongoDB

        Args:
            mongodb_url (str): URL подключения к MongoDB
            database_name (str): Название базы данных
        """
        self.mongodb_url = mongodb_url
        self.database_name = database_name
        self.client = None
        self.db = None
        self._connect()

    def _connect(self) -> bool:
        """
        Установка подключения к MongoDB

        Returns:
            bool: True если подключение успешно
        """
        try:
            self.client = MongoClient(
                self.mongodb_url,
                serverSelectionTimeoutMS=5000
            )
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            logger.info(f"Подключение к MongoDB для статистики успешно")
            return True
        except Exception as err:
            logger.error(f"Ошибка подключения для статистики: {err}")
            return False

    def get_popular_searches(self, limit: int = 5) -> List[Dict]:
        """
        Получение топ популярных запросов (уникальных по типу и ключевым параметрам, исключая page)

        Args:
            limit (int): Количество результатов

        Returns:
            List[Dict]: Список популярных запросов с указанием типа и количества
        """
        try:
            if self.db is None:
                logger.warning("Нет подключения к MongoDB")
                return []

            collection = self.db.final_project_010825_ptm_al
            
            # Создаем нормализованные параметры без поля page
            pipeline = [
                {
                    "$addFields": {
                        "normalized_params": {
                            "$switch": {
                                "branches": [
                                    {
                                        "case": {"$eq": ["$search_type", "keyword"]},
                                        "then": {"keyword": "$params.keyword"}
                                    },
                                    {
                                        "case": {"$eq": ["$search_type", "genre__years_range"]},
                                        "then": {
                                            "genre": "$params.genre",
                                            "years_range": "$params.years_range"
                                        }
                                    },
                                    {
                                        "case": {"$eq": ["$search_type", "genre"]},
                                        "then": {"genre": "$params.genre"}
                                    },
                                    {
                                        "case": {"$eq": ["$search_type", "actor"]},
                                        "then": {
                                            "actor_name": {"$ifNull": ["$params.actor_name", {"$toString": "$params.actor_id"}]}
                                        }
                                    }
                                ],
                                "default": "$params"
                            }
                        }
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "search_type": "$search_type",
                            "params": "$normalized_params"
                        },
                        "count": {"$sum": 1},
                        "last_timestamp": {"$max": "$timestamp"}
                    }
                },
                {
                    "$sort": {"count": -1, "last_timestamp": -1}
                },
                {
                    "$limit": limit
                }
            ]
            results = list(collection.aggregate(pipeline))
            return results
        except Exception as err:
            logger.error(f"Ошибка при получении популярных запросов: {err}")
            return []

    def get_recent_searches(self, limit: int = 5) -> List[Dict]:
        """
        Получение последних уникальных поисков (уникальных по типу и ключевым параметрам, исключая page)

        Args:
            limit (int): Количество результатов

        Returns:
            List[Dict]: Список последних уникальных поисков
        """
        try:
            if self.db is None:
                logger.warning("Нет подключения к MongoDB")
                return []

            collection = self.db.final_project_010825_ptm_al
            
            # Создаем нормализованные параметры и получаем последние уникальные запросы
            pipeline = [
                {
                    "$addFields": {
                        "normalized_params": {
                            "$switch": {
                                "branches": [
                                    {
                                        "case": {"$eq": ["$search_type", "keyword"]},
                                        "then": {"keyword": "$params.keyword"}
                                    },
                                    {
                                        "case": {"$eq": ["$search_type", "genre__years_range"]},
                                        "then": {
                                            "genre": "$params.genre",
                                            "years_range": "$params.years_range"
                                        }
                                    },
                                    {
                                        "case": {"$eq": ["$search_type", "genre"]},
                                        "then": {"genre": "$params.genre"}
                                    },
                                    {
                                        "case": {"$eq": ["$search_type", "actor"]},
                                        "then": {
                                            "actor_name": {"$ifNull": ["$params.actor_name", {"$toString": "$params.actor_id"}]}
                                        }
                                    }
                                ],
                                "default": "$params"
                            }
                        }
                    }
                },
                {
                    "$sort": {"timestamp": -1}
                },
                {
                    "$group": {
                        "_id": {
                            "search_type": "$search_type",
                            "params": "$normalized_params"
                        },
                        "timestamp": {"$first": "$timestamp"},
                        "results_count": {"$first": "$results_count"},
                        "execution_time_ms": {"$first": "$execution_time_ms"},
                        "search_type": {"$first": "$search_type"},
                        "params": {"$first": "$normalized_params"}
                    }
                },
                {
                    "$sort": {"timestamp": -1}
                },
                {
                    "$limit": limit
                }
            ]
            results = list(collection.aggregate(pipeline))
            return results
        except Exception as err:
            logger.error(f"Ошибка при получении последних поисков: {err}")
            return []

    def get_stats_by_type(self) -> Dict[str, int]:
        """
        Получение статистики по типам поисков

        Returns:
            Dict[str, int]: Словарь с количеством поисков по каждому типу
        """
        try:
            if self.db is None:
                logger.warning("Нет подключения к MongoDB")
                return {}

            collection = self.db.final_project_010825_ptm_al
            pipeline = [
                {
                    "$group": {
                        "_id": "$search_type",
                        "count": {"$sum": 1}
                    }
                }
            ]
            results = list(collection.aggregate(pipeline))
            stats = {result['_id']: result['count'] for result in results}
            return stats
        except Exception as err:
            logger.error(f"Ошибка при получении статистики по типам: {err}")
            return {}

    def close(self) -> None:
        """Закрытие подключения к MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Подключение к MongoDB (статистика) закрыто")
