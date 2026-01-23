"""
Класс для работы с Mongo базой данных
Класс обрабатывает все операции с базой данных и включает обработку ошибок
"""
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure
import logging

logger = logging.getLogger(__name__)


class MongoConnection:
    """Базовый класс для подключения к MongoDB"""

    def __init__(self, mongodb_url: str, database_name: str):
        self.mongodb_url = mongodb_url
        self.database_name = database_name
        self.client = None
        self.db = None
        self._connect()

    def _connect(self) -> bool:
        """Установка подключения к MongoDB с обработкой ошибок"""
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

    def close(self) -> None:
        """Закрытие подключения к MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Подключение к MongoDB закрыто")
