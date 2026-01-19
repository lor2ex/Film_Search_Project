# 📚 Полная документация проекта Film Search

## Оглавление
1. [Обзор проекта](#обзор-проекта)
2. [Архитектура](#архитектура)
3. [Модули и компоненты](#модули-и-компоненты)
4. [База данных](#база-данных)
5. [API документация](#api-документация)
6. [Frontend](#frontend)
7. [Конфигурация](#конфигурация)

---

## Обзор проекта

### Назначение
Film Search - это полнофункциональное веб-приложение для поиска фильмов из базы данных Sakila с интеграцией внешних API, логированием и аналитикой.

### Ключевые возможности
- Многокритериальный поиск фильмов (название, жанр, год, актёр)
- Интеграция с TMDB API для получения постеров
- Умное сопоставление вымышленных названий с реальными фильмами
- Логирование всех запросов в MongoDB
- Статистика популярных и последних поисков
- Современный адаптивный веб-интерфейс

### Технологии
- **Backend**: FastAPI (Python 3.9+)
- **Databases**: MySQL (Sakila), MongoDB
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **External APIs**: TMDB (The Movie Database)

---

## Архитектура

### Общая структура
```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ HTTP/AJAX
       ▼
┌─────────────┐
│   FastAPI   │ ◄─── main.py (Entry Point)
└──────┬──────┘
       │
       ├──► app/routes/films.py (API Endpoints)
       │
       ├──► app/database/mysql_connector.py (MySQL DAO)
       │    └──► MySQL Sakila DB
       │
       ├──► app/logging/log_writer.py (Logging)
       │    └──► MongoDB
       │
       ├──► app/logging/log_stats.py (Statistics)
       │    └──► MongoDB
       │
       └──► app/utils/formatter.py (TMDB API)
            └──► TMDB API
```

### Паттерны проектирования
- **DAO (Data Access Object)** - изоляция логики работы с БД
- **Repository Pattern** - абстракция доступа к данным
- **Dependency Injection** - через FastAPI
- **Singleton** - для подключений к БД

---

## Модули и компоненты

### 1. main.py - Точка входа приложения

**Назначение**: Инициализация и запуск FastAPI приложения

**Основные функции**:
```python
app = FastAPI(
    title="Film Search API",
    description="API для поиска фильмов из базы данных Sakila",
    version="1.0.0"
)
```

**Что делает**:
- Создает экземпляр FastAPI приложения
- Настраивает CORS для кросс-доменных запросов
- Подключает статические файлы (CSS, JS)
- Регистрирует маршруты из `app/routes/films.py`
- Запускает Uvicorn сервер на порту 8000

**Endpoints**:
- `GET /` - главная страница (index.html)
- `GET /health` - проверка здоровья приложения

---

### 2. app/database/mysql_connector.py - MySQL DAO

**Назначение**: Data Access Object для работы с MySQL базой данных Sakila

**Класс**: `MySQLConnector`

**Инициализация**:
```python
mysql_db = MySQLConnector(dbconfig)
```

**Методы**:

#### `_connect()` - Подключение к БД
- Устанавливает соединение с MySQL
- Обрабатывает ошибки подключения (2003, 1045)
- Логирует результат подключения

#### `_execute_query(query, params)` - Выполнение запросов
- Выполняет SELECT запросы с параметрами
- Защита от SQL injection через параметризацию
- Возвращает результаты как список словарей
- Обрабатывает ошибки выполнения

#### `search_by_keyword(keyword, page, page_size)` - Поиск по названию
```python
films, total = mysql_db.search_by_keyword("matrix", page=1, page_size=10)
```
- SQL: `SELECT ... FROM film WHERE title LIKE %keyword%`
- Возвращает: (список фильмов, общее количество)
- Постраничная навигация с OFFSET

#### `search_by_genre_and_year(genre, year_from, year_to, page, page_size)`
```python
films, total = mysql_db.search_by_genre_and_year("Action", 2000, 2010, 1, 10)
```
- SQL: JOIN с таблицами film_category и category
- Фильтрация по жанру и диапазону лет
- Возвращает уникальные фильмы (DISTINCT)

#### `search_by_genre(genre, page, page_size)` - Поиск только по жанру
- Упрощенная версия без фильтрации по годам
- Используется для быстрого поиска

#### `search_by_actor(actor_id, page, page_size)` - Поиск по актёру
```python
films, total = mysql_db.search_by_actor(actor_id=1, page=1, page_size=10)
```
- SQL: JOIN с таблицей film_actor
- Возвращает все фильмы с участием актёра

#### `get_all_genres()` - Список жанров
- Возвращает все категории из таблицы category
- Сортировка по алфавиту

#### `get_all_actors()` - Список актёров
- Возвращает первых 100 актёров
- Сортировка по имени и фамилии

#### `get_year_range()` - Диапазон лет
- MIN и MAX год выпуска из таблицы film
- Используется для настройки фильтров

#### `get_year_range_for_genre(genre)` - Диапазон для жанра
- Возвращает доступные годы для конкретного жанра
- Используется для автоматического обновления фильтров

#### `get_film_actors(film_id)` - Актёры фильма
- Возвращает список актёров для конкретного фильма
- Используется для обогащения данных

#### `get_film_categories(film_id)` - Жанры фильма
- Возвращает список жанров для фильма
- Используется для обогащения данных

#### `get_actor_by_id(actor_id)` - Информация об актёре
- Возвращает имя и фамилию актёра по ID
- Используется для логирования с именем вместо ID

**Обработка ошибок**:
- Логирование всех ошибок
- Возвращение пустых результатов при ошибках
- Graceful degradation

---

### 3. app/logging/log_writer.py - Запись логов

**Назначение**: Запись всех поисковых запросов в MongoDB

**Класс**: `LogWriter`

**Инициализация**:
```python
log_writer = LogWriter(
    mongodb_url=MONGODB_URL_WRITE,
    database_name='ich_edit',
    collection_name='final_project_010825_ptm_al'
)
```

**Методы**:

#### `_connect()` - Подключение к MongoDB
- Устанавливает соединение с MongoDB
- Проверяет подключение через ping
- Таймаут: 5 секунд для выбора сервера, 10 секунд для подключения

#### `log_search(search_type, params, results_count, execution_time_ms)`
```python
log_writer.log_search(
    search_type="keyword",
    params={"keyword": "matrix"},
    results_count=10,
    execution_time_ms=125.5
)
```

**Структура лога**:
```json
{
    "timestamp": "2026-01-13T16:04:10.326773",
    "search_type": "keyword",
    "params": {"keyword": "matrix"},
    "results_count": 10,
    "execution_time_ms": 125.5
}
```

**Типы поисков**:
- `keyword` - поиск по названию
- `genre__years_range` - поиск по жанру и году
- `genre` - поиск только по жанру
- `actor` - поиск по актёру

**Особенности**:
- Автоматическая временная метка (UTC)
- Сохранение времени выполнения запроса
- Сохранение имени актёра вместо ID
- Исключение номера страницы из параметров (для уникальности)

---

### 4. app/logging/log_stats.py - Статистика

**Назначение**: Получение статистики поисков из MongoDB

**Класс**: `LogStats`

**Инициализация**:
```python
log_stats = LogStats(
    mongodb_url=MONGODB_URL_READ,
    database_name='ich_edit'
)
```

**Методы**:

#### `get_popular_searches(limit=5)` - Популярные запросы
```python
popular = log_stats.get_popular_searches(limit=5)
```

**MongoDB Aggregation Pipeline**:
```javascript
[
    {
        $addFields: {
            normalized_params: {
                // Нормализация параметров без page
            }
        }
    },
    {
        $group: {
            _id: {
                search_type: "$search_type",
                params: "$normalized_params"
            },
            count: { $sum: 1 },
            last_timestamp: { $max: "$timestamp" }
        }
    },
    {
        $sort: { count: -1, last_timestamp: -1 }
    },
    {
        $limit: 5
    }
]
```

**Возвращает**:
```python
[
    {
        "_id": {
            "search_type": "keyword",
            "params": {"keyword": "ape"}
        },
        "count": 22,
        "last_timestamp": "2026-01-13T16:04:10"
    },
    ...
]
```

#### `get_recent_searches(limit=5)` - Последние поиски
```python
recent = log_stats.get_recent_searches(limit=5)
```

**MongoDB Aggregation Pipeline**:
- Нормализация параметров
- Сортировка по timestamp (DESC)
- Группировка по уникальным комбинациям
- Выбор первого (самого свежего) из каждой группы
- Финальная сортировка и лимит

**Возвращает**:
```python
[
    {
        "timestamp": "2026-01-13T16:04:10",
        "search_type": "keyword",
        "params": {"keyword": "ape"},
        "results_count": 10,
        "execution_time_ms": 544.54
    },
    ...
]
```

**Особенности**:
- Умная нормализация параметров (исключает page)
- Работает со старыми записями (с page) и новыми (без page)
- Гарантирует уникальность результатов
- Сортировка по частоте и времени

---

### 5. app/utils/formatter.py - Форматирование и TMDB API

**Назначение**: Форматирование данных и интеграция с TMDB API для постеров

**Функции**:

#### `format_film_response(film, actors, categories)`
```python
formatted = format_film_response(
    film={'film_id': 1, 'title': 'ACADEMY DINOSAUR', ...},
    actors=['John Doe', 'Jane Smith'],
    categories=['Action', 'Drama']
)
```

**Возвращает**:
```python
{
    "film_id": 1,
    "title": "ACADEMY DINOSAUR",
    "description": "A Epic Drama...",
    "release_year": 2006,
    "length": 86,
    "rating": "PG",
    "actors": ["John Doe", "Jane Smith"],
    "categories": ["Action", "Drama"],
    "poster": "https://image.tmdb.org/t/p/w500/..."
}
```

#### `get_poster_for_film(title, year)` - Умная система постеров

**Алгоритм работы** (5 уровней):

**Уровень 1: Прямой поиск**
```python
poster = search_movie_poster(title, year)
```
- Поиск в TMDB по оригинальному названию

**Уровень 2: Сопоставление с реальными фильмами**
```python
real_title = map_to_real_movie(title, year)
if real_title != title:
    poster = search_movie_poster(real_title, year)
```
- 60+ готовых сопоставлений
- `ACADEMY DINOSAUR` → `Jurassic Park`

**Уровень 3: Популярные фильмы по году**
```python
random_title = get_random_popular_movie(year)
poster = search_movie_poster(random_title, year)
```
- База популярных фильмов 1997-2006
- Стабильный выбор на основе хеша

**Уровень 4: Случайный популярный фильм**
```python
random_title = get_fallback_movie(title)
poster = search_movie_poster(random_title, None)
```
- 30+ топовых фильмов всех времен
- Стабильный выбор на основе хеша названия

**Уровень 5: Эмодзи резерв**
```python
return get_default_poster_emoji(title)
```
- 10 красивых эмодзи
- Стабильный выбор на основе хеша

#### `search_movie_poster(title, year)` - Поиск в TMDB
```python
poster_url = search_movie_poster("Jurassic Park", 1993)
# Возвращает: "https://image.tmdb.org/t/p/w500/kGLOLum7xU95spakBEfxCjEfNn0.jpg"
```

**Параметры запроса**:
- `api_key` - ключ TMDB API
- `query` - название фильма
- `year` - год выпуска (опционально)
- `language` - "ru-RU" для русских названий

**Обработка**:
- Таймаут 5 секунд
- Берет первый результат из поиска
- Возвращает URL постера или None

#### `map_to_real_movie(sakila_title, year)` - Сопоставление

**База сопоставлений** (60+ фильмов):
```python
sakila_to_real = {
    'ACADEMY DINOSAUR': 'Jurassic Park',
    'ACE GOLDFINGER': 'Goldfinger',
    'ADAPTATION HOLES': 'The Shawshank Redemption',
    'AFFAIR PREJUDICE': 'Pride and Prejudice',
    'AFRICAN EGG': 'The Lion King',
    'AGENT TRUMAN': 'The Truman Show',
    'AIRPLANE SIERRA': 'Top Gun',
    'ALADDIN CALENDAR': 'Aladdin',
    'ALIEN CENTER': 'Alien',
    'AMADEUS HOLY': 'Amadeus',
    # ... еще 50+ сопоставлений
}
```

#### `get_random_popular_movie(year)` - Популярные по году

**База по годам**:
```python
popular_by_year = {
    2006: ['The Departed', 'Casino Royale', 'Pirates of the Caribbean', ...],
    2005: ['Star Wars: Episode III', 'Harry Potter', ...],
    2004: ['Shrek 2', 'Spider-Man 2', ...],
    # ... 1997-2006
}
```

#### `get_fallback_movie(title)` - Резервные фильмы

**Топ-30 фильмов**:
```python
fallback_movies = [
    'The Shawshank Redemption',
    'The Godfather',
    'The Dark Knight',
    'Pulp Fiction',
    'The Matrix',
    # ... еще 25 фильмов
]
```

#### `get_default_poster_emoji(title)` - Эмодзи постеры

**10 вариантов**:
```python
default_posters = ['🎬', '🎥', '📽️', '🎞️', '🍿', '🎪', '🎭', '🎨', '🌟', '✨']
```

**Кэширование**:
```python
POSTER_CACHE = {}  # Глобальный кэш
# Ключ: "title_year" или "title"
# Значение: URL или эмодзи
```

---

### 6. app/routes/films.py - API маршруты

**Назначение**: Определение всех API endpoints для работы с фильмами

**Глобальные объекты**:
```python
mysql_db = MySQLConnector(dbconfig)
log_writer = LogWriter(MONGODB_URL_WRITE)
log_stats = LogStats(MONGODB_URL_READ)
```

**Endpoints**:

#### `GET /api/search/keyword` - Поиск по названию
```python
@router.get("/api/search/keyword")
async def search_by_keyword(
    q: str = Query(..., min_length=1, max_length=100),
    page: int = Query(1, ge=1)
)
```

**Параметры**:
- `q` - ключевое слово (обязательно, 1-100 символов)
- `page` - номер страницы (по умолчанию 1)

**Процесс**:
1. Поиск в MySQL: `mysql_db.search_by_keyword(q, page, 10)`
2. Обогащение данных (актёры, жанры, постеры)
3. Логирование в MongoDB
4. Возврат результатов

**Ответ**:
```json
{
    "total_count": 22,
    "page": 1,
    "page_size": 10,
    "films": [...]
}
```

#### `GET /api/search/genre-year` - Поиск по жанру и году
```python
@router.get("/api/search/genre-year")
async def search_by_genre_and_year(
    genre: str = Query(...),
    year_from: int = Query(2000, ge=1895, le=2030),
    year_to: int = Query(2023, ge=1895, le=2030),
    page: int = Query(1, ge=1)
)
```

**Логирование**:
```python
log_writer.log_search(
    search_type="genre__years_range",
    params={
        "genre": genre,
        "years_range": f"{year_from}-{year_to}"
    },
    results_count=len(films),
    execution_time_ms=execution_time * 1000
)
```

#### `GET /api/search/genre` - Поиск только по жанру
- Упрощенная версия без фильтрации по годам
- Быстрый поиск

#### `GET /api/search/actor` - Поиск по актёру
```python
@router.get("/api/search/actor")
async def search_by_actor(
    actor_id: int = Query(..., ge=1),
    page: int = Query(1, ge=1)
)
```

**Особенность**:
```python
# Получаем имя актёра для логирования
actor_info = mysql_db.get_actor_by_id(actor_id)
actor_name = f"{actor_info['first_name']} {actor_info['last_name']}"

log_writer.log_search(
    search_type="actor",
    params={"actor_name": actor_name},  # Имя, а не ID!
    ...
)
```

#### `GET /api/genres` - Список жанров
```python
@router.get("/api/genres", response_model=List[GenreResponse])
async def get_genres()
```

**Ответ**:
```json
[
    {"category_id": 1, "name": "Action"},
    {"category_id": 2, "name": "Animation"},
    ...
]
```

#### `GET /api/actors` - Список актёров
```python
@router.get("/api/actors", response_model=List[ActorResponse])
async def get_actors()
```

**Ответ**:
```json
[
    {
        "actor_id": 1,
        "first_name": "Penelope",
        "last_name": "Guiness",
        "full_name": "Penelope Guiness"
    },
    ...
]
```

#### `GET /api/year-range` - Диапазон лет
```python
@router.get("/api/year-range", response_model=YearRangeResponse)
async def get_year_range()
```

**Ответ**:
```json
{
    "min_year": 2000,
    "max_year": 2023
}
```

#### `GET /api/year-range-for-genre` - Диапазон для жанра
```python
@router.get("/api/year-range-for-genre")
async def get_year_range_for_genre(
    genre: str = Query(...)
)
```

**Использование**: Автоматическое обновление фильтров при выборе жанра

#### `GET /api/stats/popular` - Популярные запросы
```python
@router.get("/api/stats/popular")
async def get_popular_stats()
```

**Ответ**:
```json
{
    "popular_searches": [
        {
            "_id": {
                "search_type": "keyword",
                "params": {"keyword": "ape"}
            },
            "count": 22
        },
        ...
    ]
}
```

#### `GET /api/stats/recent` - Последние поиски
```python
@router.get("/api/stats/recent")
async def get_recent_stats()
```

**Обработка ошибок**:
- Все endpoints обернуты в try-except
- Логирование ошибок
- Возврат понятных сообщений клиенту
- Graceful degradation

---

### 7. app/models/schemas.py - Pydantic модели

**Назначение**: Валидация данных и определение структур

**Модели**:

#### `FilmBase` - Базовая модель фильма
```python
class FilmBase(BaseModel):
    film_id: int
    title: str
    description: Optional[str] = None
    release_year: int
    language_id: int
```

#### `FilmDetail` - Детальная модель
```python
class FilmDetail(FilmBase):
    length: Optional[int] = None
    rating: Optional[str] = None
    categories: Optional[List[str]] = None
    actors: Optional[List[str]] = None
```

#### `GenreResponse` - Модель жанра
```python
class GenreResponse(BaseModel):
    category_id: int
    name: str
```

#### `ActorResponse` - Модель актёра
```python
class ActorResponse(BaseModel):
    actor_id: int
    first_name: str
    last_name: str
    full_name: str
```

#### `YearRangeResponse` - Диапазон лет
```python
class YearRangeResponse(BaseModel):
    min_year: int
    max_year: int
```

**Использование**:
- Автоматическая валидация входных данных
- Генерация OpenAPI документации
- Type hints для IDE

---

## База данных

### MySQL (Sakila)

**Используемые таблицы**:

#### `film` - Фильмы
```sql
CREATE TABLE film (
    film_id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    release_year YEAR,
    language_id TINYINT UNSIGNED NOT NULL,
    length SMALLINT UNSIGNED,
    rating ENUM('G','PG','PG-13','R','NC-17'),
    PRIMARY KEY (film_id)
);
```

#### `category` - Жанры
```sql
CREATE TABLE category (
    category_id TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(25) NOT NULL,
    PRIMARY KEY (category_id)
);
```

#### `film_category` - Связь фильмов и жанров
```sql
CREATE TABLE film_category (
    film_id SMALLINT UNSIGNED NOT NULL,
    category_id TINYINT UNSIGNED NOT NULL,
    PRIMARY KEY (film_id, category_id),
    FOREIGN KEY (film_id) REFERENCES film (film_id),
    FOREIGN KEY (category_id) REFERENCES category (category_id)
);
```

#### `actor` - Актёры
```sql
CREATE TABLE actor (
    actor_id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    first_name VARCHAR(45) NOT NULL,
    last_name VARCHAR(45) NOT NULL,
    PRIMARY KEY (actor_id)
);
```

#### `film_actor` - Связь фильмов и актёров
```sql
CREATE TABLE film_actor (
    actor_id SMALLINT UNSIGNED NOT NULL,
    film_id SMALLINT UNSIGNED NOT NULL,
    PRIMARY KEY (actor_id, film_id),
    FOREIGN KEY (actor_id) REFERENCES actor (actor_id),
    FOREIGN KEY (film_id) REFERENCES film (film_id)
);
```

**Индексы**:
- PRIMARY KEY на всех таблицах
- FOREIGN KEY для связей
- Индексы на часто используемых полях (title, name)

### MongoDB

**База данных**: `ich_edit`
**Коллекция**: `final_project_010825_ptm_al`

**Структура документа**:
```json
{
    "_id": ObjectId("..."),
    "timestamp": "2026-01-13T16:04:10.326773",
    "search_type": "keyword",
    "params": {
        "keyword": "ape"
    },
    "results_count": 10,
    "execution_time_ms": 544.54
}
```

**Индексы** (рекомендуемые):
```javascript
db.final_project_010825_ptm_al.createIndex({ "timestamp": -1 })
db.final_project_010825_ptm_al.createIndex({ "search_type": 1 })
db.final_project_010825_ptm_al.createIndex({ "search_type": 1, "params": 1 })
```

---

## Frontend

### static/index.html - Главная страница

**Структура**:
```html
<div class="container">
    <header class="header">
        <h1>🎬 Film Search</h1>
    </header>
    
    <main class="main-content">
        <!-- Вкладки навигации -->
        <div class="tabs">
            <button class="tab-button active">По названию</button>
            <button class="tab-button">По жанру и году</button>
            <button class="tab-button">По актёру</button>
            <button class="tab-button">Статистика</button>
        </div>
        
        <!-- Контент вкладок -->
        <div id="keyword" class="tab-content active">...</div>
        <div id="genre" class="tab-content">...</div>
        <div id="actor" class="tab-content">...</div>
        <div id="stats" class="tab-content">...</div>
    </main>
</div>
```

**Формы поиска**:
- Поле ввода для ключевого слова
- Выпадающий список жанров
- Поля для диапазона лет
- Выпадающий список актёров

### static/js/script.js - JavaScript логика

**Глобальные переменные**:
```javascript
const API_BASE = '/api';
window.currentSearchFunction = null;  // Для пагинации
```

**Основные функции**:

#### `switchTab(tabName)` - Переключение вкладок
```javascript
function switchTab(tabName) {
    // Скрыть все вкладки
    // Показать выбранную
    // Загрузить данные при необходимости
}
```

#### `searchByKeyword(page)` - Поиск по названию
```javascript
async function searchByKeyword(page = 1) {
    const keyword = document.getElementById('keyword-input').value.trim();
    
    // Сохраняем функцию для пагинации
    window.currentSearchFunction = (p) => searchByKeyword(p);
    
    // AJAX запрос
    const response = await fetch(`${API_BASE}/search/keyword?q=${keyword}&page=${page}`);
    const data = await response.json();
    
    // Отображение результатов
    displayResults('keyword-results', data.films, data.total_count, data.page, data.page_size);
}
```

#### `searchByGenreYear(page)` - Поиск по жанру и году
```javascript
async function searchByGenreYear(page = 1) {
    const genre = document.getElementById('genre-select').value;
    const yearFrom = parseInt(document.getElementById('year-from').value);
    const yearTo = parseInt(document.getElementById('year-to').value);
    
    // Валидация
    if (yearFrom > yearTo) {
        showError('genre-results', 'Год начала не может быть больше года конца');
        return;
    }
    
    // AJAX запрос и отображение
}
```

#### `searchByActor(page)` - Поиск по актёру
```javascript
async function searchByActor(page = 1) {
    const actorId = document.getElementById('actor-select').value;
    
    // AJAX запрос к /api/search/actor
}
```

#### `displayResults(containerId, films, totalCount, currentPage, pageSize)`
```javascript
function displayResults(containerId, films, totalCount, currentPage, pageSize) {
    // Создание HTML для карточек фильмов
    let html = '<div class="film-grid">';
    
    films.forEach(film => {
        // Определение типа постера (URL или эмодзи)
        let posterElement;
        if (film.poster && film.poster.startsWith('http')) {
            posterElement = `<img src="${film.poster}" ...>`;
        } else {
            posterElement = `<div class="film-poster-emoji">${film.poster}</div>`;
        }
        
        // Создание карточки фильма
        html += `
            <div class="film-card">
                <div class="film-poster">${posterElement}</div>
                <div class="film-info">
                    <div class="film-title">${film.title}</div>
                    <div class="film-year">📅 ${film.release_year}</div>
                    <div class="film-description">${film.description}</div>
                    <div class="film-metadata">
                        <!-- Длительность, рейтинг, актёры, жанры -->
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    
    // Добавление пагинации
    if (totalPages > 1) {
        html += '<div class="pagination">...</div>';
    }
    
    container.innerHTML = html;
}
```

#### `loadGenres()` - Загрузка жанров
```javascript
async function loadGenres() {
    const response = await fetch(`${API_BASE}/genres`);
    const genres = await response.json();
    
    // Заполнение select
    const select = document.getElementById('genre-select');
    genres.forEach(genre => {
        const option = document.createElement('option');
        option.value = genre.name;
        option.textContent = genre.name;
        select.appendChild(option);
    });
    
    // Обработчик изменения жанра
    select.addEventListener('change', async function() {
        if (this.value) {
            await updateYearRangeForGenre(this.value);
        }
    });
}
```

#### `updateYearRangeForGenre(genre)` - Обновление диапазона лет
```javascript
async function updateYearRangeForGenre(genre) {
    const response = await fetch(`${API_BASE}/year-range-for-genre?genre=${genre}`);
    const data = await response.json();
    
    // Обновление полей ввода
    document.getElementById('year-from').value = data.min_year;
    document.getElementById('year-to').value = data.max_year;
    
    // Показ информационного сообщения
    const genreResults = document.getElementById('genre-results');
    genreResults.innerHTML = `
        <div class="info-message">
            📅 Для жанра "${genre}" доступны фильмы с ${data.min_year} по ${data.max_year} год
        </div>
    `;
}
```

#### `loadStats()` - Загрузка статистики
```javascript
async function loadStats() {
    // Популярные запросы
    const popularResponse = await fetch(`${API_BASE}/stats/popular`);
    const popularData = await popularResponse.json();
    displayPopularStats(popularData.popular_searches);
    
    // Последние поиски
    const recentResponse = await fetch(`${API_BASE}/stats/recent`);
    const recentData = await recentResponse.json();
    displayRecentStats(recentData.recent_searches);
}
```

#### `displayPopularStats(searches)` - Отображение популярных
```javascript
function displayPopularStats(searches) {
    let html = '';
    searches.forEach((item, index) => {
        const searchType = item._id?.search_type || item.search_type;
        const params = item._id?.params || item.params;
        
        // Определение типа и параметров
        let typeLabel = '';
        let paramsText = '';
        
        if (searchType === 'keyword') {
            typeLabel = '🔤 Поиск по названию';
            paramsText = `"${params.keyword}"`;
        } else if (searchType === 'genre__years_range') {
            typeLabel = '🎭 Поиск по жанру и году';
            paramsText = `${params.genre} (${params.years_range})`;
        } else if (searchType === 'actor') {
            typeLabel = '👥 Поиск по актёру';
            paramsText = params.actor_name;
        }
        
        html += `
            <div class="stat-item">
                <div class="stat-type">${index + 1}. ${typeLabel}</div>
                <div class="stat-params">Параметры: ${paramsText}</div>
                <div class="stat-count">Выполнено: ${item.count} раз(а)</div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}
```

**Вспомогательные функции**:
- `showLoading(containerId)` - показать индикатор загрузки
- `showError(containerId, message)` - показать ошибку
- `escapeHtml(text)` - экранирование HTML

**Инициализация**:
```javascript
document.addEventListener('DOMContentLoaded', () => {
    loadYearRange();
    loadGenres();
    loadActors();
    
    // Поддержка Enter в полях ввода
    document.getElementById('keyword-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchByKeyword(1);
    });
});
```

---

### static/css/styles.css - Стили

**Дизайн система**: Perplexity Design System

**CSS Variables**:
```css
:root {
    /* Цвета */
    --color-background: var(--color-cream-50);
    --color-surface: var(--color-cream-100);
    --color-text: var(--color-slate-900);
    --color-primary: var(--color-teal-500);
    
    /* Типографика */
    --font-family-base: "FKGroteskNeue", "Geist", "Inter", sans-serif;
    --font-size-base: 14px;
    --line-height-normal: 1.5;
    
    /* Отступы */
    --space-8: 8px;
    --space-16: 16px;
    --space-24: 24px;
    
    /* Радиусы */
    --radius-base: 8px;
    --radius-lg: 12px;
    
    /* Тени */
    --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.04);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.04);
}
```

**Темная тема**:
```css
@media (prefers-color-scheme: dark) {
    :root {
        --color-background: var(--color-charcoal-700);
        --color-surface: var(--color-charcoal-800);
        --color-text: var(--color-gray-200);
        --color-primary: var(--color-teal-300);
    }
}
```

**Ключевые классы**:

#### Карточки фильмов
```css
.film-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: var(--space-24);
    align-items: start;
}

.film-card {
    background: var(--color-surface);
    border: 1px solid var(--color-card-border);
    border-radius: var(--radius-lg);
    display: flex;
    flex-direction: column;
    height: 100%;
}

.film-poster {
    width: 100%;
    height: 400px;  /* Фиксированная высота */
    overflow: hidden;
}

.film-poster-image {
    width: 100%;
    height: 100%;
    object-fit: cover;  /* Пропорциональное обрезание */
    object-position: center top;
}

.film-info {
    padding: var(--space-16);
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    min-height: 200px;
}

.film-title {
    color: var(--color-primary);
    font-size: var(--font-size-xl);
    font-weight: var(--font-weight-semibold);
    min-height: 2.4em;  /* Резерв для 2 строк */
}

.film-description {
    flex-grow: 1;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 3;  /* Ограничение до 3 строк */
    -webkit-box-orient: vertical;
}

.film-metadata {
    margin-top: auto;  /* Прижимаем к низу */
    padding-top: var(--space-8);
    border-top: 1px solid var(--color-card-border-inner);
}
```

#### Пагинация
```css
.pagination {
    display: flex;
    justify-content: center;
    gap: var(--space-8);
    margin-top: var(--space-32);
}

.page-button {
    padding: var(--space-8) var(--space-16);
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    cursor: pointer;
    border-radius: var(--radius-base);
}

.page-button.active {
    background: var(--color-primary);
    color: var(--color-btn-primary-text);
}
```

#### Статистика
```css
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: var(--space-24);
}

.stat-item {
    background: var(--color-secondary);
    border-left: 4px solid var(--color-primary);
    padding: var(--space-16);
    border-radius: var(--radius-sm);
}
```

**Адаптивность**:
```css
@media (max-width: 768px) {
    .film-grid {
        grid-template-columns: 1fr;
    }
    
    .film-poster {
        height: 320px;
    }
    
    .stats-grid {
        grid-template-columns: 1fr;
    }
}
```

---

## Конфигурация

### local_settings.py - Настройки БД

**MySQL конфигурация**:
```python
HOST = 'ich-db.edu.itcareerhub.de'
USER = 'ich1'
PASSWORD = 'password'
DATABASE = 'sakila'

dbconfig = {
    'host': HOST,
    'user': USER,
    'password': PASSWORD,
    'database': DATABASE,
}
```

**MongoDB конфигурация**:
```python
MONGODB_URL_READ = 'mongodb://user:pass@host:port/?authSource=db'
MONGODB_URL_WRITE = 'mongodb://user:pass@host:port/?authSource=db'
```

**Важно**: Этот файл не должен попадать в Git!

### tmdb_config.py - TMDB API

```python
TMDB_API_KEY = "your_tmdb_api_key_here"
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
```

**Получение ключа**: См. [TMDB_SETUP.md](TMDB_SETUP.md)

### requirements.txt - Зависимости

```
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
mysql-connector-python==8.2.0
pymongo==4.6.0
python-multipart==0.0.6
requests==2.31.0
```

---

## Потоки данных

### Поиск фильма (полный цикл)

```
1. Пользователь вводит "matrix" и нажимает "Поиск"
   ↓
2. JavaScript: searchByKeyword(1)
   ↓
3. AJAX запрос: GET /api/search/keyword?q=matrix&page=1
   ↓
4. FastAPI: films.py → search_by_keyword()
   ↓
5. MySQL: mysql_connector.py → search_by_keyword("matrix", 1, 10)
   ↓
6. SQL: SELECT * FROM film WHERE title LIKE '%matrix%' LIMIT 10 OFFSET 0
   ↓
7. Обогащение данных:
   - get_film_actors(film_id) для каждого фильма
   - get_film_categories(film_id) для каждого фильма
   - get_poster_for_film(title, year) для каждого фильма
   ↓
8. TMDB API (если настроен):
   - Сопоставление: "MATRIX SOMETHING" → "The Matrix"
   - Поиск постера в TMDB
   - Возврат URL или эмодзи
   ↓
9. Логирование в MongoDB:
   - log_writer.log_search(...)
   - Сохранение в коллекцию
   ↓
10. Возврат JSON клиенту:
    {
        "total_count": 3,
        "page": 1,
        "page_size": 10,
        "films": [...]
    }
   ↓
11. JavaScript: displayResults()
    - Создание HTML карточек
    - Отображение постеров
    - Добавление пагинации
   ↓
12. Пользователь видит результаты
```

### Получение статистики

```
1. Пользователь открывает вкладку "Статистика"
   ↓
2. JavaScript: loadStats()
   ↓
3. Два параллельных запроса:
   - GET /api/stats/popular
   - GET /api/stats/recent
   ↓
4. MongoDB Aggregation:
   - Нормализация параметров
   - Группировка по уникальным комбинациям
   - Сортировка и лимит
   ↓
5. Возврат данных клиенту
   ↓
6. JavaScript:
   - displayPopularStats()
   - displayRecentStats()
   ↓
7. Пользователь видит статистику
```

---

## Безопасность

### SQL Injection Protection
```python
# ❌ Небезопасно
query = f"SELECT * FROM film WHERE title LIKE '%{keyword}%'"

# ✅ Безопасно
query = "SELECT * FROM film WHERE title LIKE %s"
cursor.execute(query, (f"%{keyword}%",))
```

### XSS Protection
```javascript
// ❌ Небезопасно
element.innerHTML = film.title;

// ✅ Безопасно
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}
element.innerHTML = escapeHtml(film.title);
```

### CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В production указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Секретные данные
```python
# .gitignore
local_settings.py
tmdb_config.py
*.log
__pycache__/
.venv/
```

---

## Производительность

### Кэширование постеров
```python
POSTER_CACHE = {}  # In-memory кэш

# При первом запросе
poster = get_poster_for_film("Matrix", 1999)
# → Запрос к TMDB API
# → Сохранение в POSTER_CACHE["Matrix_1999"]

# При повторном запросе
poster = get_poster_for_film("Matrix", 1999)
# → Возврат из POSTER_CACHE (без запроса к API)
```

### Пагинация
```python
# Вместо загрузки всех результатов
films = mysql_db.search_by_keyword("matrix", page=1, page_size=10)
# → LIMIT 10 OFFSET 0

# Следующая страница
films = mysql_db.search_by_keyword("matrix", page=2, page_size=10)
# → LIMIT 10 OFFSET 10
```

### MongoDB Aggregation
```javascript
// Вместо загрузки всех документов и фильтрации в Python
// Используем aggregation pipeline на стороне MongoDB
db.collection.aggregate([
    { $group: ... },
    { $sort: ... },
    { $limit: 5 }
])
```

---

## Тестирование

### Ручное тестирование

**Поиск по названию**:
1. Ввести "ape" → Ожидается: 10+ результатов
2. Ввести "xyz123" → Ожидается: "Фильмы не найдены"
3. Пагинация → Ожидается: корректная навигация

**Поиск по жанру**:
1. Выбрать "Action" → Ожидается: обновление диапазона лет
2. Установить годы 2000-2010 → Ожидается: фильмы в диапазоне
3. Выбрать другой жанр → Ожидается: новый диапазон

**Статистика**:
1. Выполнить несколько поисков
2. Открыть вкладку "Статистика"
3. Проверить отображение популярных и последних
4. Убедиться в отсутствии дублей

**Постеры**:
1. С TMDB API → Ожидается: настоящие постеры
2. Без API → Ожидается: эмодзи постеры
3. Ошибка загрузки → Ожидается: fallback на эмодзи

---

## Развертывание

### Production рекомендации

**1. Переменные окружения**:
```python
import os

MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://localhost:27017')
TMDB_API_KEY = os.getenv('TMDB_API_KEY', '')
```

**2. Gunicorn вместо Uvicorn**:
```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

**3. Nginx reverse proxy**:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /static {
        alias /path/to/static;
    }
}
```

**4. Логирование**:
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

**5. Мониторинг**:
- Health check endpoint: `/health`
- Логирование ошибок
- Мониторинг производительности БД

---

## Заключение

Этот проект демонстрирует:
- ✅ Полный цикл разработки веб-приложения
- ✅ Работу с несколькими базами данных (MySQL, MongoDB)
- ✅ Интеграцию с внешними API (TMDB)
- ✅ Современный адаптивный интерфейс
- ✅ Логирование и аналитику
- ✅ Обработку ошибок и безопасность
- ✅ Соблюдение best practices (PEP8, модульность)

**Автор**: Проект Film Search  
**Дата**: Январь 2026  
**Версия**: 1.0.0