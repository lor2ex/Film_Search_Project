/**
 * Film Search Project - JavaScript функции
 * Обработка AJAX запросов и управление UI
 */

const API_BASE = '/api';

// Глобальная переменная для хранения текущей функции поиска
window.currentSearchFunction = null;

// ===== ПЕРЕКЛЮЧЕНИЕ ВКЛАДОК =====

function switchTab(tabName) {
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => tab.classList.remove('active'));

    const buttons = document.querySelectorAll('.tab-button');
    buttons.forEach(btn => btn.classList.remove('active'));

    document.getElementById(tabName).classList.add('active');
    event.target.classList.add('active');

    // Загрузка данных при открытии вкладок
    if (tabName === 'genre') {
        loadGenres();
    } else if (tabName === 'year') {
        loadYearRange();
    } else if (tabName === 'actor') {
        loadActors();
    } else if (tabName === 'stats') {
        loadStats();
    }
}

// ===== ЗАГРУЗКА ЖАНРОВ =====

async function loadGenres() {
    try {
        const response = await fetch(`${API_BASE}/genres`);
        const genres = await response.json();

        const select = document.getElementById('genre-select');
        select.innerHTML = '<option value="">-- Выберите жанр --</option>';

        genres.forEach(genre => {
            const option = document.createElement('option');
            option.value = genre.name;
            option.textContent = genre.name;
            select.appendChild(option);
        });

        // Добавляем обработчик изменения жанра для автоматического обновления диапазона лет
        select.addEventListener('change', async function() {
            if (this.value) {
                await updateYearRangeForGenre(this.value);
            } else {
                await loadYearRange(); // Загружаем общий диапазон лет
            }
        });
    } catch (error) {
        console.error('Ошибка при загрузке жанров:', error);
    }
}

// ===== ОБНОВЛЕНИЕ ДИАПАЗОНА ЛЕТ ДЛЯ ЖАНРА =====

async function updateYearRangeForGenre(genre) {
    try {
        const response = await fetch(`${API_BASE}/year-range-for-genre?genre=${encodeURIComponent(genre)}`);
        const data = await response.json();

        document.getElementById('year-from').value = data.min_year;
        document.getElementById('year-from').min = data.min_year;

        document.getElementById('year-to').value = data.max_year;
        document.getElementById('year-to').max = data.max_year;

        // Показываем пользователю информацию о диапазоне
        const genreResults = document.getElementById('genre-results');
        genreResults.innerHTML = `
            <div class="info-message">
                📅 Для жанра "${genre}" доступны фильмы с ${data.min_year} по ${data.max_year} год
            </div>
        `;
    } catch (error) {
        console.error('Ошибка при загрузке диапазона лет для жанра:', error);
    }
}

// ===== ЗАГРУЗКА АКТЁРОВ =====

async function loadActors() {
    try {
        const response = await fetch(`${API_BASE}/actors`);
        const actors = await response.json();

        const select = document.getElementById('actor-select');
        select.innerHTML = '<option value="">-- Выберите актёра --</option>';

        actors.forEach(actor => {
            const option = document.createElement('option');
            option.value = actor.actor_id;
            option.textContent = actor.full_name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Ошибка при загрузке актёров:', error);
    }
}

// ===== ЗАГРУЗКА ДИАПАЗОНА ЛЕТ =====

async function loadYearRange() {
    try {
        const response = await fetch(`${API_BASE}/year-range`);
        const data = await response.json();

        document.getElementById('year-from').value = data.min_year;
        document.getElementById('year-from').min = data.min_year;

        document.getElementById('year-to').value = data.max_year;
        document.getElementById('year-to').max = data.max_year;
    } catch (error) {
        console.error('Ошибка при загрузке диапазона лет:', error);
    }
}

// ===== ПОИСК ПО КЛЮЧЕВОМУ СЛОВУ =====

async function searchByKeyword(page = 1) {
    const keyword = document.getElementById('keyword-input').value.trim();

    if (!keyword) {
        showError('keyword-results', 'Пожалуйста, введите название фильма');
        return;
    }

    // Сохраняем функцию поиска для пагинации
    window.currentSearchFunction = (p) => searchByKeyword(p);

    showLoading('keyword-results');

    try {
        const response = await fetch(
            `${API_BASE}/search/keyword?q=${encodeURIComponent(keyword)}&page=${page}`
        );
        const data = await response.json();

        if (data.error) {
            showError('keyword-results', data.message || 'Ошибка при поиске');
            return;
        }

        displayResults(
            'keyword-results',
            data.films,
            data.total_count,
            data.page,
            data.page_size
        );
    } catch (error) {
        console.error('Ошибка:', error);
        showError('keyword-results', 'Ошибка подключения к серверу');
    }
}

// ===== ПОИСК ПО ЖАНРУ И ГОДУ =====

async function searchByGenreYear(page = 1) {
    const genre = document.getElementById('genre-select').value;
    const yearFrom = parseInt(document.getElementById('year-from').value);
    const yearTo = parseInt(document.getElementById('year-to').value);

    if (!genre) {
        showError('genre-results', 'Пожалуйста, выберите жанр');
        return;
    }

    if (yearFrom > yearTo) {
        showError('genre-results', 'Год начала не может быть больше года конца');
        return;
    }

    // Сохраняем функцию поиска для пагинации
    window.currentSearchFunction = (p) => searchByGenreYear(p);

    showLoading('genre-results');

    try {
        const response = await fetch(
            `${API_BASE}/search/genre-year?genre=${encodeURIComponent(genre)}&year_from=${yearFrom}&year_to=${yearTo}&page=${page}`
        );
        const data = await response.json();

        if (data.error) {
            showError('genre-results', data.message || 'Ошибка при поиске');
            return;
        }

        displayResults(
            'genre-results',
            data.films,
            data.total_count,
            data.page,
            data.page_size
        );
    } catch (error) {
        console.error('Ошибка:', error);
        showError('genre-results', 'Ошибка подключения к серверу');
    }
}

// ===== ПОИСК ПО ГОДУ =====

async function searchByYear(page = 1) {
    const yearFrom = parseInt(document.getElementById('year-from').value);
    const yearTo = parseInt(document.getElementById('year-to').value);

    if (yearFrom > yearTo) {
        showError('year-results', 'Год начала не может быть больше года конца');
        return;
    }

    // Сохраняем функцию поиска для пагинации
    window.currentSearchFunction = (p) => searchByYear(p);

    showLoading('year-results');

    try {
        const response = await fetch(
            `${API_BASE}/search/year?year_from=${yearFrom}&year_to=${yearTo}&page=${page}`
        );
        const data = await response.json();

        if (data.error) {
            showError('year-results', data.message || 'Ошибка при поиске');
            return;
        }

        displayResults(
            'year-results',
            data.films,
            data.total_count,
            data.page,
            data.page_size
        );
    } catch (error) {
        console.error('Ошибка:', error);
        showError('year-results', 'Ошибка подключения к серверу');
    }
}

// ===== ПОИСК ПО ИМЕНИ АКТЁРА =====

async function searchByActorName(page = 1) {
    const name = document.getElementById('actor-name-input').value.trim();

    if (!name) {
        showError('actor-results', 'Пожалуйста, введите имя или фамилию актёра');
        return;
    }

    // Сохраняем функцию поиска для пагинации
    window.currentSearchFunction = (p) => searchByActorName(p);

    showLoading('actor-results');

    try {
        const response = await fetch(
            `${API_BASE}/search/actor-by-name?name=${encodeURIComponent(name)}&page=${page}`
        );
        const data = await response.json();

        if (data.error) {
            showError('actor-results', data.message || 'Ошибка при поиске');
            return;
        }

        displayResults(
            'actor-results',
            data.films,
            data.total_count,
            data.page,
            data.page_size
        );
    } catch (error) {
        console.error('Ошибка:', error);
        showError('actor-results', 'Ошибка подключения к серверу');
    }
}

// ===== ПОИСК ПО АКТЁРУ =====

async function searchByActor(page = 1) {
    const actorId = document.getElementById('actor-select').value;

    if (!actorId) {
        showError('actor-results', 'Пожалуйста, выберите актёра');
        return;
    }

    // Сохраняем функцию поиска для пагинации
    window.currentSearchFunction = (p) => searchByActor(p);

    showLoading('actor-results');

    try {
        const response = await fetch(
            `${API_BASE}/search/actor?actor_id=${actorId}&page=${page}`
        );
        const data = await response.json();

        if (data.error) {
            showError('actor-results', data.message || 'Ошибка при поиске');
            return;
        }

        displayResults(
            'actor-results',
            data.films,
            data.total_count,
            data.page,
            data.page_size
        );
    } catch (error) {
        console.error('Ошибка:', error);
        showError('actor-results', 'Ошибка подключения к серверу');
    }
}

// ===== ОТОБРАЖЕНИЕ РЕЗУЛЬТАТОВ С ПАГИНАЦИЕЙ =====

function displayResults(containerId, films, totalCount, currentPage, pageSize) {
    const container = document.getElementById(containerId);

    if (!films || films.length === 0) {
        container.innerHTML = '<div class="no-results">❌ Фильмы не найдены</div>';
        return;
    }

    let html = '<div class="film-grid">';

    films.forEach(film => {
        const description = film.description || 'Описание отсутствует';
        const length = film.length ? `⏱️ ${film.length} мин` : '';
        const rating = film.rating ? `<span class="film-rating">${film.rating}</span>` : '';
        const actors = film.actors && film.actors.length > 0
            ? `<div class="film-actors">
                 <span class="film-actors-label">👥 Актёры:</span>
                 <span class="film-actors-text">${film.actors.slice(0, 3).join(', ')}${film.actors.length > 3 ? '...' : ''}</span>
               </div>`
            : '';
        const categories = film.categories && film.categories.length > 0
            ? `<div class="film-categories">
                 <span class="film-categories-label">🎭 Жанры:</span>
                 <span class="film-categories-text">${film.categories.join(', ')}</span>
               </div>`
            : '';

        // Определяем тип постера и создаем соответствующий элемент
        let posterElement;
        if (film.poster && film.poster.startsWith('http')) {
            // Это URL изображения
            posterElement = `<img src="${film.poster}" alt="${escapeHtml(film.title)}" class="film-poster-image" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                            <div class="film-poster-fallback" style="display:none;">🎬</div>`;
        } else {
            // Это эмодзи
            posterElement = `<div class="film-poster-emoji">${film.poster || '🎬'}</div>`;
        }

        html += `
            <div class="film-card">
                <div class="film-poster">
                    ${posterElement}
                </div>
                <div class="film-info">
                    <div class="film-title">${escapeHtml(film.title)}</div>
                    <div class="film-year">📅 ${film.release_year}</div>
                    <div class="film-description">${escapeHtml(description)}</div>
                    
                    <div class="film-metadata">
                        ${length ? `<div class="film-length">${length}</div>` : ''}
                        ${rating}
                        ${actors}
                        ${categories}
                    </div>
                </div>
            </div>
        `;
    });

    html += '</div>';

    // Добавление pagination
    const totalPages = Math.ceil(totalCount / pageSize);
    if (totalPages > 1) {
        html += '<div class="pagination">';

        // Предыдущая страница
        if (currentPage > 1) {
            html += `<button class="page-button" onclick="window.currentSearchFunction(${currentPage - 1})">← Назад</button>`;
        }

        // Номера страниц
        for (let i = 1; i <= Math.min(totalPages, 5); i++) {
            const activeClass = i === currentPage ? 'active' : '';
            html += `<button class="page-button ${activeClass}" onclick="window.currentSearchFunction(${i})">${i}</button>`;
        }

        if (totalPages > 5) {
            html += '<span style="color: var(--light-text); padding: 0 10px;">...</span>';
        }

        // Следующая страница
        if (currentPage < totalPages) {
            html += `<button class="page-button" onclick="window.currentSearchFunction(${currentPage + 1})">Вперёд →</button>`;
        }

        html += '</div>';
    }

    container.innerHTML = html;
}

// ===== СТАТИСТИКА =====

async function loadStats() {
    showLoading('popular-stats');
    showLoading('recent-stats');

    try {
        const popularResponse = await fetch(`${API_BASE}/stats/popular`);
        const popularData = await popularResponse.json();
        displayPopularStats(popularData.popular_searches);

        const recentResponse = await fetch(`${API_BASE}/stats/recent`);
        const recentData = await recentResponse.json();
        displayRecentStats(recentData.recent_searches);
    } catch (error) {
        console.error('Ошибка при загрузке статистики:', error);
        showError('popular-stats', 'Ошибка при загрузке данных');
        showError('recent-stats', 'Ошибка при загрузке данных');
    }
}

function displayPopularStats(searches) {
    const container = document.getElementById('popular-stats');

    if (!searches || searches.length === 0) {
        container.innerHTML = '<div class="no-results">Нет данных</div>';
        return;
    }

    let html = '';
    searches.forEach((item, index) => {
        // Обрабатываем как старую, так и новую структуру данных
        const searchType = item._id?.search_type || item.search_type;
        const params = item._id?.params || item.params;
        let typeLabel = '';
        let paramsText = '';

        if (searchType === 'keyword') {
            typeLabel = '🔤 Поиск по названию';
            paramsText = `"${params.keyword}"`;
        } else if (searchType === 'genre__years_range') {
            typeLabel = '🎭 Поиск по жанру и году';
            paramsText = `${params.genre} (${params.years_range})`;
        } else if (searchType === 'genre') {
            typeLabel = '🎭 Поиск по жанру';
            paramsText = params.genre;
        } else if (searchType === 'actor') {
            typeLabel = '👥 Поиск по актёру';
            paramsText = params.actor_name || `ID: ${params.actor_id}`;
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

function displayRecentStats(searches) {
    const container = document.getElementById('recent-stats');

    if (!searches || searches.length === 0) {
        container.innerHTML = '<div class="no-results">Нет данных</div>';
        return;
    }

    let html = '';
    searches.forEach((item, index) => {
        const time = new Date(item.timestamp).toLocaleString('ru-RU');
        let typeLabel = '';
        let paramsText = '';

        if (item.search_type === 'keyword') {
            typeLabel = '🔤 Поиск по названию';
            paramsText = `"${item.params.keyword}"`;
        } else if (item.search_type === 'genre__years_range') {
            typeLabel = '🎭 Поиск по жанру и году';
            paramsText = `${item.params.genre} (${item.params.years_range})`;
        } else if (item.search_type === 'genre') {
            typeLabel = '🎭 Поиск по жанру';
            paramsText = item.params.genre;
        } else if (item.search_type === 'actor') {
            typeLabel = '👥 Поиск по актёру';
            paramsText = item.params.actor_name || `ID: ${item.params.actor_id}`;
        }

        html += `
            <div class="stat-item">
                <div class="stat-type">${index + 1}. ${typeLabel}</div>
                <div class="stat-params">Параметры: ${paramsText}</div>
                <div class="stat-value">Результатов: ${item.results_count}</div>
                <div class="stat-time">⏱️ ${item.execution_time_ms.toFixed(2)}ms | ${time}</div>
            </div>
        `;
    });

    container.innerHTML = html;
}

// ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

function showLoading(containerId) {
    const container = document.getElementById(containerId);
    container.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>Загрузка...</p>
        </div>
    `;
}

function showError(containerId, message) {
    const container = document.getElementById(containerId);
    container.innerHTML = `<div class="error">⚠️ ${escapeHtml(message)}</div>`;
}

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

// ===== ИНИЦИАЛИЗАЦИЯ =====

document.addEventListener('DOMContentLoaded', () => {
    loadYearRange();
    loadGenres();
    loadActors();

    // Поддержка Enter в поле ввода
    document.getElementById('keyword-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            searchByKeyword(1);
        }
    });

    document.getElementById('actor-name-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            searchByActorName(1);
        }
    });
});
