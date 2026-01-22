"""
Модуль для получения статистики поисков из MongoDB
"""

from app.database.mongo_connection import MongoConnection
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class LogStats(MongoConnection):
    """Класс для получения статистики поисковых запросов из MongoDB"""

    def __init__(self, mongodb_url: str, database_name: str = 'ich_edit'):
        super().__init__(mongodb_url, database_name)

    def get_popular_searches(self, limit: int = 5) -> List[Dict]:
        """
        Получение топ популярных запросов

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
            
            # Простая группировка по типу поиска и параметрам
            pipeline = [
                {
                    "$group": {
                        "_id": {
                            "search_type": "$search_type",
                            "params": "$params"
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
        Получение последних уникальных поисков

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
            
            # Простая сортировка по времени с группировкой
            pipeline = [
                {
                    "$sort": {"timestamp": -1}
                },
                {
                    "$group": {
                        "_id": {
                            "search_type": "$search_type",
                            "params": "$params"
                        },
                        "timestamp": {"$first": "$timestamp"},
                        "results_count": {"$first": "$results_count"},
                        "execution_time_ms": {"$first": "$execution_time_ms"},
                        "search_type": {"$first": "$search_type"},
                        "params": {"$first": "$params"}
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
