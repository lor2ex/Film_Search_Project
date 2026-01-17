# 🏗️ Архитектура Film Search Project

## Обзор архитектуры

```
┌─────────────────────────────────────────────────────────────┐
│                    WEB BROWSER                               │
│            (HTML, CSS, JavaScript)                           │
└─────────────────────┬───────────────────────────────────────┘
                      │ AJAX запросы / JSON ответы
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                  FASTAPI SERVER (main.py)                    │
│  ┌───────────────────────────────────────────────────────┐   │
│  │ Router: /api/search/keyword                           │   │
│  │ Router: /api/search/genre-year                        │   │
│  │ Router: /api/search/actor                             │   │
│  │ Router: /api/genres, /api/actors, /api/year-range     │   │
│  │ Router: /api/stats/popular, /api/stats/recent         │   │
│  └───────────────────────────────────────────────────────┘   │
└────┬────────────────────────────┬─────────────────────────┬──┘
     │                            │                         │
     ↓                            ↓                         ↓
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  MySQL Database  │    │   MongoDB WRITE  │    │   Static Files   │
│   (Sakila)       │    │   (Logging)      │    │  (CSS, JS, HTML) │
│                  │    │                  │    │                  │
│ • film           │    │ • search_logs    │    │ /static/css      │
│ • actor          │    │   - timestamp    │    │ /static/js       │
│ • category       │    │   - search_type  │    │ /static/index.html
│ • film_actor     │    │   - params       │    │                  │
│ • film_category  │    │   - results_count│    │                  │
│                  │    │   - exec_time    │    │                  │
└──────────────────┘    └──────────────────┘    └──────────────────┘
```

---

## Слои приложения

### 1️⃣ PRESENTATION LAYER (Слой представления)
**Файлы:** `static/index.html`, `static/css/styles.css`, `static/js/script.js`

**Ответственность:**
- HTML структура с вкладками
- CSS стили (тёмная зелёная тема)
- JavaScript для AJAX запросов
- Отображение результатов и статистики

**Ключевые функции:**
```javascript
switchTab()          // Переключение вкладок
searchByKeyword()    // AJAX поиск по названию
searchByGenreYear()  // AJAX поиск по жанру
searchByActor()      // AJAX поиск по актёру
loadStats()          // Загрузка статистики
```

---

### 2️⃣ API LAYER (Слой API)
**Файл:** `app/routes/films.py`

**Ответственность:**
- FastAPI маршруты и endpoints
- Валидация входных данных (Query параметры)
- Обработка HTTP запросов
- Возврат JSON ответов

**Endpoints:**
```
GET /api/search/keyword      (q, page)
GET /api/search/genre-year   (genre, year_from, year_to, page)
GET /api/search/actor        (actor_id, page)
GET /api/genres              ()
GET /api/actors              ()
GET /api/year-range          ()
GET /api/stats/popular       ()
GET /api/stats/recent        ()
```

---

### 3️⃣ DATA ACCESS LAYER (DAO слой)
**Файл:** `app/database/mysql_connector.py`

**Ответственность:**
- Подключение к MySQL БД
- Выполнение SQL запросов
- Обработка ошибок БД
- Логирование операций

**Ключевые классы:**
```python
class MySQLConnector:
    def __init__(config)           # Подключение
    def search_by_keyword()        # Поиск по названию
    def search_by_genre_and_year() # Поиск по жанру/году
    def search_by_actor()          # Поиск по актёру
    def get_all_genres()           # Список жанров
    def get_all_actors()           # Список актёров
    def get_film_actors()          # Актёры фильма
    def get_film_categories()      # Жанры фильма
```

---

### 4️⃣ LOGGING LAYER (Слой логирования)
**Файлы:** `app/logging/log_writer.py`, `app/logging/log_stats.py`

**Ответственность:**
- Запись логов в MongoDB
- Получение статистики из MongoDB
- Обработка подключения к MongoDB

**Ключевые классы:**
```python
class LogWriter:
    def __init__(mongodb_url)  # Подключение
    def log_search()           # Логирование поиска

class LogStats:
    def __init__(mongodb_url)  # Подключение
    def get_popular_searches() # Популярные запросы
    def get_recent_searches()  # Последние запросы
    def get_stats_by_type()    # Статистика по типам
```

---

### 5️⃣ MODEL LAYER (Слой моделей)
**Файл:** `app/models/schemas.py`

**Ответственность:**
- Pydantic модели для валидации
- Определение структуры данных
- Type checking

**Ключевые модели:**
```python
FilmBase        # Базовые данные фильма
FilmDetail      # Полные данные с актёрами
GenreResponse   # Ответ для жанра
ActorResponse   # Ответ для актёра
SearchResponse  # Ответ результатов поиска
```

---

### 6️⃣ UTILITY LAYER (Вспомогательный слой)
**Файл:** `app/utils/formatter.py`

**Ответственность:**
- Форматирование данных
- Обрезание текста
- Функции-помощники

**Ключевые функции:**
```python
format_film_response()     # Форматирование фильма
format_actor_name()        # Форматирование имени
truncate_description()     # Обрезание текста
```

---

## Поток данных

### Сценарий 1: Поиск по ключевому слову

```
1. Пользователь вводит "matrix" в input
2. JavaScript вызывает searchByKeyword()
3. AJAX запрос к /api/search/keyword?q=matrix&page=1
4. FastAPI обработчик вызывает mysql_db.search_by_keyword()
5. MySQLConnector выполняет SQL запрос к БД Sakila
6. Результаты обогащаются данными об актёрах и жанрах
7. LogWriter записывает лог в MongoDB
8. API возвращает JSON с результатами
9. JavaScript отображает карточки фильмов
```

---

### Сценарий 2: Загрузка статистики

```
1. Пользователь переходит на вкладку "Статистика"
2. JavaScript вызывает loadStats()
3. AJAX запросы к:
   - /api/stats/popular
   - /api/stats/recent
4. FastAPI обработчики вызывают log_stats методы
5. LogStats выполняет MongoDB aggregation pipeline
6. Результаты возвращаются в JSON
7. JavaScript отображает статистику на странице
```

---

## Обработка ошибок

### MySQL ошибки (MySQLConnector)
```python
try:
    connection = mysql.connector.connect(**config)
except Error as err:
    if err.errno == 2003:       # Сервер недоступен
        logger.error("Сервер недоступен")
    elif err.errno == 1045:     # Неверные учётные данные
        logger.error("Неверные учётные данные")
    else:
        logger.error(f"Ошибка: {err}")
```

### MongoDB ошибки (LogWriter, LogStats)
```python
try:
    client = MongoClient(mongodb_url, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
except (ServerSelectionTimeoutError, ConnectionFailure) as err:
    logger.error(f"Ошибка подключения к MongoDB: {err}")
```

### API ошибки (films.py)
```python
try:
    films, total_count = mysql_db.search_by_keyword(q, page)
except Exception as e:
    logger.error(f"Ошибка при поиске: {e}")
    return {"error": "Ошибка при поиске", "message": str(e)}
```

---

## Безопасность

### 1. SQL Injection Protection
Используются параметризованные запросы:
```python
query = "SELECT * FROM film WHERE title LIKE %s"
cursor.execute(query, (f"%{keyword}%",))  # Параметр отделён
```

### 2. XSS Protection
HTML экранирование в JavaScript:
```javascript
function escapeHtml(text) {
    const map = {'&': '&amp;', '<': '&lt;', '>': '&gt;', ...};
    return text.replace(/[&<>"']/g, m => map[m]);
}
```

### 3. CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить все origins
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Performance Optimization

### Database Queries
- ✅ Используются `LIMIT` для постраничной навигации
- ✅ Индексы на часто используемых полях
- ✅ JOIN операции оптимизированы

### Caching (Возможное улучшение)
```python
# Например, кэширование списка жанров
@app.get("/api/genres")
@cache(expire=3600)  # Кэширование на 1 час
async def get_genres():
    ...
```

### Lazy Loading (Возможное улучшение)
```javascript
// Загрузка актёров и жанров только при переходе на вкладку
if (tabName === 'genre') {
    loadGenres();  // Загрузка по требованию
}
```

---

## Масштабируемость

### Текущая архитектура
```
Single FastAPI server
     ↓
Single MySQL instance
     ↓
Single MongoDB instance
```

### Масштабированная архитектура (будущее)
```
Load Balancer
    ↓
[FastAPI 1] [FastAPI 2] [FastAPI 3]
    ↓
MySQL Cluster (Primary + Replicas)
    ↓
MongoDB Cluster (Sharded)
```

---

## Тестирование (примеры)

### Unit Testing
```python
def test_mysql_connector():
    connector = MySQLConnector(test_config)
    films, count = connector.search_by_keyword("matrix", 1)
    assert count > 0
    assert len(films) > 0

def test_formatter():
    result = format_film_response(film, actors, categories)
    assert result['title'] == film['title']
```

### Integration Testing
```python
def test_api_search_keyword():
    response = client.get("/api/search/keyword?q=matrix&page=1")
    assert response.status_code == 200
    assert response.json()['total_count'] > 0
```

---

## Мониторинг и логирование

### Логирование в коде
```python
import logging
logger = logging.getLogger(__name__)

logger.info("Подключение к БД успешно")
logger.error("Ошибка подключения: ...")
```

### Логирование в MongoDB
```json
{
  "timestamp": "2026-01-11T15:34:00",
  "search_type": "keyword",
  "params": {"keyword": "matrix"},
  "results_count": 3,
  "execution_time_ms": 125.5
}
```

### Health Check Endpoint
```python
@app.get("/health")
async def health_check():
    return {"status": "ok"}
```

---

## Развёртывание

### Локальное развёртывание
```bash
python main.py
# Приложение доступно на http://localhost:8000
```

### Production развёртывание (Gunicorn)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 main:app
```

### Docker развёртывание (Dockerfile)
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

---

## Заключение

Архитектура приложения следует классическому паттерну MVC с хорошим разделением ответственности:

✅ **Модульность** - каждый слой независим
✅ **Масштабируемость** - легко добавлять новые функции
✅ **Поддерживаемость** - код хорошо организован и документирован
✅ **Безопасность** - защита от основных уязвимостей
✅ **Производительность** - оптимизированные запросы

**Идеально подходит для учебного проекта и может быть расширено в production приложение.**
