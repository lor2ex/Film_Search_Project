"""
Модуль для логирования поисковых запросов в MongoDB
"""

from app.database.mongo_connection import MongoConnection
from typing import Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class LogWriter(MongoConnection):
    """Класс для записи логов поисковых запросов в MongoDB"""

    def __init__(self, mongodb_url: str, database_name: str = 'ich_edit',
                 collection_name: str = "final_project_010825_ptm_al"):
        self.collection_name = collection_name
        super().__init__(mongodb_url, database_name)

    def log_search(self, search_type: str, params: Dict,
                   results_count: int, execution_time_ms: float) -> bool:
        """Логирование поискового запроса в MongoDB"""
        try:
            if self.db is None:
                logger.warning("Нет подключения к MongoDB")
                return False

            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "search_type": search_type,
                "params": params,
                "results_count": results_count,
                "execution_time_ms": execution_time_ms
            }

            collection = self.db[self.collection_name]
            result = collection.insert_one(log_entry)
            logger.info(f"Лог сохранён в коллекцию '{self.collection_name}': {result.inserted_id}")
            return True
        except Exception as err:
            logger.error(f"Ошибка при сохранении лога: {err}")
            return False
