import { setupTheme } from './theme.js';
import { get } from './api.js';
import { renderTaskCard, updateCardInDOM, closeAllDropdowns } from './card.js';
import { showToast } from './ui/toast.js';
import {
    setUsers,
    getUsers,
    getWeekStart,
    setWeekStart,
    getWeekRange,
    setLastLoadedWeek,
    getLastLoadedWeek,
    setWeekTasks,
    getWeekTasks,
    updateTaskInWeekState,
    clearCalendarCache,
} from './state.js';

setupTheme();

const MONTH_NAMES = [
    'Январь', 'Февраль', 'Март', 'Апрель',
    'Май', 'Июнь', 'Июль', 'Август',
    'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
];

const WEEKDAY_NAMES = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];

const appEl = document.getElementById('app');

function todayStr() {
    const d = new Date();
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
}

function isToday(dateStr) {
    return dateStr === todayStr();
}

function isOverdueDate(dateStr) {
    return dateStr < todayStr();
}

function getWeekStartForDate(dateStr) {
    const d = new Date(dateStr + 'T00:00:00');
    const dow = d.getDay();
    const offset = dow === 0 ? -6 : 1 - dow;
    const monday = new Date(d);
    monday.setDate(d.getDate() + offset);
    monday.setHours(0, 0, 0, 0);
    return monday.toISOString().split('T')[0];
}

function getCurrentWeekStart() {
    return getWeekStartForDate(todayStr());
}

function isCurrentWeek() {
    return getWeekStart() === getCurrentWeekStart();
}

function addWeekDays(dateStr, delta) {
    const d = new Date(dateStr + 'T00:00:00');
    d.setDate(d.getDate() + delta * 7);
    return d.toISOString().split('T')[0];
}

function formatDateForDisplay(dateStr) {
    const d = new Date(dateStr + 'T00:00:00');
    return `${d.getDate()}`;
}

function getOrCreateContainer() {
    let container = appEl.querySelector('.calendar-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'calendar-container';
        appEl.appendChild(container);
    }
    return container;
}

function clearContainer() {
    appEl.innerHTML = '';
}

function renderNav(weekStartStr) {
    const container = getOrCreateContainer();
    let nav = container.querySelector('.calendar-nav');
    if (!nav) {
        nav = document.createElement('div');
        nav.className = 'calendar-nav';
        container.insertBefore(nav, container.firstChild);
    }

    nav.innerHTML = '';

    const prevBtn = document.createElement('button');
    prevBtn.className = 'nav-prev';
    prevBtn.textContent = '\u2039';
    prevBtn.title = 'Предыдущая неделя';
    prevBtn.setAttribute('aria-label', 'Предыдущая неделя');
    prevBtn.addEventListener('click', () => changeWeek(-1));

    const nextBtn = document.createElement('button');
    nextBtn.className = 'nav-next';
    nextBtn.textContent = '\u203A';
    nextBtn.title = 'Следующая неделя';
    nextBtn.setAttribute('aria-label', 'Следующая неделя');
    nextBtn.addEventListener('click', () => changeWeek(1));

    if (isCurrentWeek()) {
        nextBtn.style.display = 'none';
    }

    const todayBtn = document.createElement('button');
    todayBtn.className = 'nav-today';
    todayBtn.textContent = 'Сегодня';
    todayBtn.title = 'Перейти к текущей неделе';
    todayBtn.setAttribute('aria-label', 'Сегодня');
    todayBtn.style.fontWeight = '600';
    todayBtn.style.fontSize = '0.85rem';
    todayBtn.style.width = 'auto';
    todayBtn.style.padding = '0 0.6rem';

    if (isCurrentWeek()) {
        todayBtn.disabled = true;
        todayBtn.style.opacity = '0.5';
        todayBtn.style.cursor = 'default';
    } else {
        todayBtn.addEventListener('click', goToToday);
    }

    const startD = new Date(weekStartStr + 'T00:00:00');
    const endD = new Date(startD);
    endD.setDate(startD.getDate() + 6);

    const title = document.createElement('span');
    title.className = 'calendar-month-title';
    title.textContent = `Пн ${startD.getDate()} – Вс ${endD.getDate()} ${MONTH_NAMES[endD.getMonth()]} ${endD.getFullYear()}`;

    nav.appendChild(prevBtn);
    nav.appendChild(todayBtn);
    nav.appendChild(nextBtn);
    nav.appendChild(title);
}

function buildWeekGrid(weekStartStr) {
    const container = getOrCreateContainer();
    let grid = container.querySelector('.calendar-grid');
    if (!grid) {
        grid = document.createElement('div');
        grid.className = 'calendar-grid';
        container.appendChild(grid);
    }

    grid.innerHTML = '';

    for (const name of WEEKDAY_NAMES) {
        const hc = document.createElement('div');
        hc.className = 'calendar-header-cell';
        hc.textContent = name;
        grid.appendChild(hc);
    }

    const today = todayStr();

    for (let i = 0; i < 7; i++) {
        const d = new Date(weekStartStr + 'T00:00:00');
        d.setDate(d.getDate() + i);
        const dateStr = d.toISOString().split('T')[0];

        const cell = document.createElement('div');
        cell.className = 'calendar-day-cell';

        if (dateStr === today) {
            cell.classList.add('today');
        }

        if (isOverdueDate(dateStr)) {
            cell.classList.add('overdue-day');
        }

        const numEl = document.createElement('span');
        numEl.className = 'calendar-day-number';
        numEl.textContent = d.getDate();
        cell.appendChild(numEl);

        const tasksEl = document.createElement('div');
        tasksEl.className = 'calendar-day-tasks';
        tasksEl.dataset.date = dateStr;
        cell.appendChild(tasksEl);

        grid.appendChild(cell);
    }
}

function onCardRefresh(updatedTask) {
    const weekStart = getWeekStart();
    updateTaskInWeekState(weekStart, updatedTask.id, (t) => {
        Object.assign(t, updatedTask);
    });
    const cardEl = document.querySelector(`.calendar-task-card[data-task-id="${updatedTask.id}"]`);
    if (cardEl) {
        updateCardInDOM(cardEl, updatedTask);
    } else {
        const { start, end } = getWeekRange();
        loadWeek(start, end);
    }
}

function populateWeekTasks(daysData) {
    const taskContainers = document.querySelectorAll('.calendar-day-tasks');
    let hasAnyTasks = false;

    for (const tc of taskContainers) {
        const dateKey = tc.dataset.date;
        const tasks = daysData[dateKey] || [];

        if (tasks.length === 0) {
            continue;
        }

        hasAnyTasks = true;

        for (const task of tasks) {
            const card = renderTaskCard(task, onCardRefresh);
            card._onCardRefresh = onCardRefresh;
            tc.appendChild(card);
        }
    }

    if (!hasAnyTasks) {
        const grid = document.querySelector('.calendar-grid');
        if (grid) {
            const empty = document.createElement('div');
            empty.className = 'calendar-empty';
            empty.textContent = 'В этой неделе задач нет. Создайте шаблон в админке, чтобы начать.';
            grid.appendChild(empty);
        }
    }
}

function showLoading() {
    clearContainer();
    const container = getOrCreateContainer();
    const loader = document.createElement('div');
    loader.className = 'calendar-loading';
    loader.textContent = 'Загрузка…';
    container.appendChild(loader);
}

function hideLoading() {
    const container = getOrCreateContainer();
    const loader = container.querySelector('.calendar-loading');
    if (loader) {
        loader.remove();
    }
}

function showError(message) {
    const grid = document.querySelector('.calendar-grid');
    if (grid) {
        grid.innerHTML = '';
    }

    const gridEl = document.querySelector('.calendar-grid') || createGrid();
    const err = document.createElement('div');
    err.className = 'calendar-error';

    const msg = document.createElement('span');
    msg.textContent = message || 'Не удалось загрузить календарь';
    err.appendChild(msg);

    const hint = document.createElement('span');
    hint.style.fontSize = '0.8rem';
    hint.style.color = 'var(--text-muted)';
    hint.textContent = 'Проверьте, что бэкенд запущен и доступен';
    err.appendChild(hint);

    const btn = document.createElement('button');
    btn.textContent = 'Повторить';
    btn.setAttribute('aria-label', 'Повторить загрузку');
    btn.addEventListener('click', () => {
        const { start, end } = getWeekRange();
        loadWeek(start, end);
    });
    err.appendChild(btn);

    gridEl.appendChild(err);
}

function createGrid() {
    const container = getOrCreateContainer();
    const grid = document.createElement('div');
    grid.className = 'calendar-grid';
    container.appendChild(grid);
    return grid;
}

async function loadWeek(start, end) {
    const cached = getWeekTasks(start);
    if (cached) {
        setWeekStart(start);
        setLastLoadedWeek(start);
        renderNav(start);
        buildWeekGrid(start);
        populateWeekTasks(cached);
        return;
    }

    showLoading();

    try {
        const data = await get(`/calendar/range?start=${start}&end=${end}`);

        setWeekStart(start);
        setLastLoadedWeek(start);
        setUsers(data.users || []);

        const daysData = data.days || {};
        setWeekTasks(start, daysData);

        renderNav(start);
        buildWeekGrid(start);
        populateWeekTasks(daysData);
        hideLoading();
    } catch (err) {
        hideLoading();
        const msg = err?.message || 'Не удалось подключиться к серверу';
        if (err.name === 'AbortError') return;
        showError(msg);
    }
}

function changeWeek(delta) {
    const currentStart = getWeekStart();
    const newStart = addWeekDays(currentStart, delta);

    if (delta > 0) {
        const currentWeekStart = getCurrentWeekStart();
        if (newStart >= currentWeekStart) {
            showToast('Переход к будущим неделям недоступен', 'error');
            return;
        }
    }

    setWeekStart(newStart);
    clearCalendarCache();
    closeAllDropdowns();
    loadWeek(newStart, addWeekDays(newStart, 1));
}

function goToToday() {
    const currentWeekStart = getCurrentWeekStart();
    setWeekStart(currentWeekStart);
    clearCalendarCache();
    closeAllDropdowns();
    const { start, end } = getWeekRange();
    loadWeek(start, end);
}

function init() {
    const currentWeekStart = getCurrentWeekStart();
    setWeekStart(currentWeekStart);
    const { start, end } = getWeekRange();
    loadWeek(start, end);
}

init();
