"""
Вспомогательные функции для форматирования и обработки данных
"""

from typing import List, Dict, Optional
import requests
import logging
import os
import sys

# Добавляем путь к корневой директории
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from tmdb_config import TMDB_API_KEY, TMDB_BASE_URL, TMDB_IMAGE_BASE_URL
except ImportError:
    # Дефолтные значения если конфиг не найден
    TMDB_API_KEY = "your_api_key_here"
    TMDB_BASE_URL = "https://api.themoviedb.org/3"
    TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

logger = logging.getLogger(__name__)

# Кэш для постеров (чтобы не делать повторные запросы)
POSTER_CACHE = {}


def format_film_response(film: Dict, actors: List[str], categories: List[str]) -> Dict:
    """
    Форматирование ответа о фильме

    Args:
        film (Dict): Информация о фильме из БД
        actors (List[str]): Список актёров
        categories (List[str]): Список категорий

    Returns:
        Dict: Отформатированный ответ
    """
    poster_url = get_poster_for_film(film.get('title', ''), film.get('release_year'))
    
    return {
        "film_id": film.get('film_id'),
        "title": film.get('title'),
        "description": film.get('description'),
        "release_year": film.get('release_year'),
        "length": film.get('length'),
        "rating": film.get('rating'),
        "actors": actors,
        "categories": categories,
        "poster": poster_url
    }


def get_poster_for_film(title: str, year: Optional[int] = None) -> str:
    """
    Получение постера фильма через TMDB API с умным сопоставлением

    Args:
        title (str): Название фильма (может быть вымышленным)
        year (Optional[int]): Год выпуска фильма

    Returns:
        str: URL постера или дефолтный эмодзи
    """
    if not title:
        return get_default_poster_emoji(title)
    
    # Если API ключ не настроен, возвращаем эмодзи
    if TMDB_API_KEY == "your_api_key_here" or not TMDB_API_KEY:
        logger.info(f"TMDB API ключ не настроен, используем эмодзи для '{title}'")
        return get_default_poster_emoji(title)
    
    # Создаем уникальный ключ для кэша
    cache_key = f"{title}_{year}" if year else title
    
    # Проверяем кэш
    if cache_key in POSTER_CACHE:
        return POSTER_CACHE[cache_key]
    
    # Пытаемся найти постер несколькими способами
    poster_url = None
    
    try:
        # Способ 1: Прямой поиск по названию
        poster_url = search_movie_poster(title, year)
        
        # Способ 2: Поиск по сопоставлению с реальными фильмами
        if not poster_url:
            real_title = map_to_real_movie(title, year)
            if real_title != title:
                logger.info(f"Сопоставляем '{title}' с реальным фильмом '{real_title}'")
                poster_url = search_movie_poster(real_title, year)
        
        # Способ 3: Генерация случайного популярного фильма по году
        if not poster_url and year:
            random_title = get_random_popular_movie(year)
            if random_title:
                logger.info(f"Используем случайный популярный фильм '{random_title}' для '{title}'")
                poster_url = search_movie_poster(random_title, year)
        
        # Способ 4: Популярные фильмы без привязки к году
        if not poster_url:
            random_title = get_fallback_movie(title)
            logger.info(f"Используем резервный фильм '{random_title}' для '{title}'")
            poster_url = search_movie_poster(random_title, None)
        
        if poster_url:
            POSTER_CACHE[cache_key] = poster_url
            return poster_url
        
        # Если ничего не найдено, используем эмодзи
        logger.info(f"Постер не найден для '{title}', используем эмодзи")
        default_poster = get_default_poster_emoji(title)
        POSTER_CACHE[cache_key] = default_poster
        return default_poster
        
    except Exception as e:
        logger.warning(f"Ошибка при получении постера для '{title}': {e}")
        default_poster = get_default_poster_emoji(title)
        POSTER_CACHE[cache_key] = default_poster
        return default_poster


def search_movie_poster(title: str, year: Optional[int] = None) -> Optional[str]:
    """
    Поиск постера фильма в TMDB

    Args:
        title (str): Название фильма
        year (Optional[int]): Год выпуска

    Returns:
        Optional[str]: URL постера или None
    """
    try:
        search_url = f"{TMDB_BASE_URL}/search/movie"
        params = {
            "api_key": TMDB_API_KEY,
            "query": title,
            "language": "ru-RU"
        }
        
        if year:
            params["year"] = year
        
        response = requests.get(search_url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            if results:
                movie = results[0]
                poster_path = movie.get('poster_path')
                
                if poster_path:
                    return f"{TMDB_IMAGE_BASE_URL}{poster_path}"
        
        return None
        
    except Exception as e:
        logger.warning(f"Ошибка поиска в TMDB для '{title}': {e}")
        return None


def map_to_real_movie(sakila_title: str, year: Optional[int] = None) -> str:
    """
    Сопоставление вымышленных названий Sakila с реальными фильмами

    Args:
        sakila_title (str): Вымышленное название из Sakila
        year (Optional[int]): Год выпуска

    Returns:
        str: Реальное название фильма или исходное название
    """
    # Словарь сопоставлений вымышленных названий с реальными
    sakila_to_real = {
        # Экшн фильмы
        'ACADEMY DINOSAUR': 'Jurassic Park',
        'ACE GOLDFINGER': 'Goldfinger',
        'ADAPTATION HOLES': 'The Shawshank Redemption',
        'AFFAIR PREJUDICE': 'Pride and Prejudice',
        'AFRICAN EGG': 'The Lion King',
        'AGENT TRUMAN': 'The Truman Show',
        'AIRPLANE SIERRA': 'Top Gun',
        'AIRPORT POLLOCK': 'Airport',
        'ALABAMA DEVIL': 'The Devil Wears Prada',
        'ALADDIN CALENDAR': 'Aladdin',
        'ALAMO VIDEOTAPE': 'The Alamo',
        'ALASKA PHANTOM': 'The Phantom',
        'ALI FOREVER': 'Ali',
        'ALICE FANTASIA': 'Alice in Wonderland',
        'ALIEN CENTER': 'Alien',
        'ALLEY EVOLUTION': 'Evolution',
        'ALONE TRIP': 'Into the Wild',
        'ALTER VICTORY': 'Victory',
        'AMADEUS HOLY': 'Amadeus',
        'AMELIE HELLFIGHTERS': 'Amélie',
        
        # Комедии
        'AMERICAN CIRCUS': 'The Greatest Showman',
        'AMISTAD MIDSUMMER': 'Amistad',
        'ANALYZE HOOSIERS': 'Hoosiers',
        'ANGELS LIFE': 'Life is Beautiful',
        'ANNIE IDENTITY': 'The Bourne Identity',
        'ANONYMOUS HUMAN': 'The Matrix',
        'ANTHEM LUKE': 'Star Wars',
        'ANTITRUST TOMATOES': 'Attack of the Killer Tomatoes',
        'ANYTHING SAVANNAH': 'Forrest Gump',
        'APACHE DIVINE': 'Dances with Wolves',
        
        # Драмы
        'APOCALYPSE FLAMINGOS': 'Apocalypse Now',
        'ARABIA DOGMA': 'Lawrence of Arabia',
        'ARACHNOPHOBIA ROLLERCOASTER': 'Arachnophobia',
        'ARGONAUTS TOWN': 'Jason and the Argonauts',
        'ARIZONA BANG': 'Raising Arizona',
        'ARK RIDGEMONT': 'Fast Times at Ridgemont High',
        'ARMAGEDDON LOST': 'Armageddon',
        'ARMY FLINTSTONES': 'The Flintstones',
        'ARTIST COLDBLOODED': 'The Artist',
        'ATLANTIS CAUSE': 'Atlantis: The Lost Empire',
        
        # Ужасы
        'ATTACK NOON': 'High Noon',
        'ATTRACTION NEWTON': 'The Theory of Everything',
        'AUTUMN CROW': 'The Crow',
        'BABY HALL': 'Baby Driver',
        'BACHELOR JAWBREAKER': 'Jawbreaker',
        'BADMAN DAWN': 'Batman Begins',
        'BAG BEETHOVEN': 'Beethoven',
        'BALLOON HOMEWARD': 'Homeward Bound',
        'BANG KWAI': 'The Bridge on the River Kwai',
        'BANGER PINOCCHIO': 'Pinocchio',
        
        # Научная фантастика
        'BARBARELLA STREETCAR': 'Barbarella',
        'BAREFOOT MANCHURIAN': 'The Manchurian Candidate',
        'BASIC EASY': 'Easy Rider',
        'BEACH HEARTBREAKERS': 'Heartbreakers',
        'BEAR GRACELAND': 'Graceland',
        'BEAST HUNCHBACK': 'The Hunchback of Notre Dame',
        'BEAUTY GREASE': 'Grease',
        'BED HIGHBALL': 'High Society',
        'BEDAZZLED MARRIED': 'Bedazzled',
        'BEETHOVEN EXORCIST': 'The Exorcist'
    }
    
    # Проверяем прямое сопоставление
    if sakila_title.upper() in sakila_to_real:
        return sakila_to_real[sakila_title.upper()]
    
    # Если прямого сопоставления нет, возвращаем исходное название
    return sakila_title


def get_random_popular_movie(year: Optional[int] = None) -> Optional[str]:
    """
    Получение случайного популярного фильма по году

    Args:
        year (Optional[int]): Год выпуска

    Returns:
        Optional[str]: Название популярного фильма
    """
    # Популярные фильмы по годам
    popular_by_year = {
        2006: ['The Departed', 'Casino Royale', 'Pirates of the Caribbean: Dead Man\'s Chest', 'The Devil Wears Prada', 'Ice Age: The Meltdown'],
        2005: ['Star Wars: Episode III', 'Harry Potter and the Goblet of Fire', 'The Chronicles of Narnia', 'War of the Worlds', 'King Kong'],
        2004: ['Shrek 2', 'Spider-Man 2', 'The Incredibles', 'Harry Potter and the Prisoner of Azkaban', 'I, Robot'],
        2003: ['Finding Nemo', 'The Lord of the Rings: The Return of the King', 'Pirates of the Caribbean', 'The Matrix Reloaded', 'X2: X-Men United'],
        2002: ['Spider-Man', 'The Lord of the Rings: The Two Towers', 'Star Wars: Episode II', 'Harry Potter and the Chamber of Secrets', 'Ice Age'],
        2001: ['Harry Potter and the Philosopher\'s Stone', 'The Lord of the Rings: The Fellowship of the Ring', 'Shrek', 'Monsters, Inc.', 'The Fast and the Furious'],
        2000: ['Gladiator', 'Cast Away', 'What Women Want', 'Dinosaur', 'How the Grinch Stole Christmas'],
        1999: ['Star Wars: Episode I', 'The Sixth Sense', 'Toy Story 2', 'Austin Powers: The Spy Who Shagged Me', 'The Matrix'],
        1998: ['Titanic', 'Armageddon', 'Saving Private Ryan', 'There\'s Something About Mary', 'The Truman Show'],
        1997: ['The Lost World: Jurassic Park', 'Men in Black', 'Tomorrow Never Dies', 'Air Force One', 'As Good as It Gets']
    }
    
    if year and year in popular_by_year:
        movies = popular_by_year[year]
        # Используем хеш для стабильного выбора
        index = abs(hash(str(year))) % len(movies)
        return movies[index]
    
    return None


def get_fallback_movie(title: str) -> str:
    """
    Получение резервного популярного фильма на основе хеша названия

    Args:
        title (str): Исходное название

    Returns:
        str: Название популярного фильма
    """
    # Список популярных фильмов для резерва
    fallback_movies = [
        'The Shawshank Redemption', 'The Godfather', 'The Dark Knight', 'Pulp Fiction',
        'The Lord of the Rings: The Return of the King', 'Forrest Gump', 'Star Wars',
        'The Matrix', 'Goodfellas', 'One Flew Over the Cuckoo\'s Nest', 'Inception',
        'The Empire Strikes Back', 'The Silence of the Lambs', 'Saving Private Ryan',
        'Schindler\'s List', 'Casablanca', 'The Departed', 'The Prestige',
        'Gladiator', 'Titanic', 'The Lion King', 'Back to the Future',
        'Terminator 2: Judgment Day', 'Alien', 'Raiders of the Lost Ark',
        'Jurassic Park', 'The Avengers', 'Iron Man', 'Spider-Man', 'Batman Begins'
    ]
    
    # Используем хеш названия для стабильного выбора
    index = abs(hash(title)) % len(fallback_movies)
    return fallback_movies[index]


def get_default_poster_emoji(title: str) -> str:
    """
    Получение дефолтного эмодзи постера на основе названия фильма

    Args:
        title (str): Название фильма

    Returns:
        str: Эмодзи постер
    """
    # Дефолтные постеры
    default_posters = ['🎬', '🎥', '📽️', '🎞️', '🍿', '🎪', '🎭', '🎨', '🌟', '✨']
    
    # Используем хеш названия для стабильного выбора
    if title:
        poster_index = abs(hash(title)) % len(default_posters)
        return default_posters[poster_index]
    
    return '🎬'


def format_actor_name(first_name: str, last_name: str) -> str:
    """
    Форматирование полного имени актёра

    Args:
        first_name (str): Имя
        last_name (str): Фамилия

    Returns:
        str: Полное имя
    """
    return f"{first_name} {last_name}"


def truncate_description(description: str, max_length: int = 200) -> str:
    """
    Обрезание описания до максимальной длины

    Args:
        description (str): Полное описание
        max_length (int): Максимальная длина

    Returns:
        str: Обрезанное описание с многоточием
    """
    if not description:
        return ""
    if len(description) <= max_length:
        return description
    return description[:max_length] + "..."
