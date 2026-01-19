"""
Модуль для логирования поисковых запросов в MongoDB
"""

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure
from typing import Dict, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)



class LogWriter:
    """
    Класс для записи логов поисковых запросов в MongoDB
    """

    def __init__(self, mongodb_url: str, database_name: str = 'ich_edit', collection_name: str = "final_project_010825_ptm_al"):
        """
        Инициализация подключения к MongoDB

        Args:
            mongodb_url (str): URL подключения к MongoDB
            database_name (str): Название базы данных
            collection_name (str): Название коллекции
        """
        self.mongodb_url = mongodb_url
        self.database_name = database_name
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self._connect()

    def _connect(self) -> bool:
        """
        Установка подключения к MongoDB с обработкой ошибок

        Returns:
            bool: True если подключение успешно, False в противном случае
        """
        try:
            self.client = MongoClient(
                self.mongodb_url,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000
            )
            # Проверка подключения
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            logger.info(f"Подключение к MongoDB успешно: {self.database_name}")
            return True
        except (ServerSelectionTimeoutError, ConnectionFailure) as err:
            logger.error(f"Ошибка подключения к MongoDB: {err}")
            return False
        except Exception as err:
            logger.error(f"Неизвестная ошибка при подключении к MongoDB: {err}")
            return False

    def log_search(
        self,
        search_type: str,
        params: Dict,
        results_count: int,
        execution_time_ms: float
    ) -> bool:
        """
        Логирование поискового запроса в MongoDB

        Args:
            search_type (str): Тип поиска (keyword, genre, year, actor)
            params (Dict): Параметры поиска
            results_count (int): Количество найденных результатов
            execution_time_ms (float): Время выполнения в миллисекундах

        Returns:
            bool: True если логирование успешно, False в противном случае
        """
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

    def close(self) -> None:
        """Закрытие подключения к MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Подключение к MongoDB закрыто")
