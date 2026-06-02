import { setupTheme } from './theme.js';
import { get } from './api.js';
import { renderTaskCard, updateCardInDOM, closeAllDropdowns } from './card.js';
import {
    setUsers,
    getUsers,
    setCurrentMonth,
    getCurrentMonth,
    setCalendarTasks,
    getCalendarTasks,
    updateTaskInState,
    clearCalendarCache,
} from './state.js';

setupTheme();

function getMaxVisibleCards() {
    return window.innerWidth <= 600 ? Infinity : 3;
}

const MONTH_NAMES = [
    'Январь', 'Февраль', 'Март', 'Апрель',
    'Май', 'Июнь', 'Июль', 'Август',
    'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
];

const WEEKDAY_NAMES = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];

const appEl = document.getElementById('app');

function todayKey() {
    const d = new Date();
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
}

function isToday(year, month, day) {
    const t = new Date();
    return t.getFullYear() === year && t.getMonth() + 1 === month && t.getDate() === day;
}

function isOverdueDate(dateStr) {
    const today = todayKey();
    return dateStr < today;
}

function daysInMonth(year, month) {
    return new Date(year, month, 0).getDate();
}

function firstDayOfMonth(year, month) {
    let dow = new Date(year, month - 1, 1).getDay();
    return dow === 0 ? 6 : dow - 1;
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

function renderNav(year, month) {
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
    prevBtn.title = 'Предыдущий месяц';
    prevBtn.setAttribute('aria-label', 'Предыдущий месяц');
    prevBtn.addEventListener('click', () => changeMonth(-1));

    const nextBtn = document.createElement('button');
    nextBtn.className = 'nav-next';
    nextBtn.textContent = '\u203A';
    nextBtn.title = 'Следующий месяц';
    nextBtn.setAttribute('aria-label', 'Следующий месяц');
    nextBtn.addEventListener('click', () => changeMonth(1));

    const todayBtn = document.createElement('button');
    todayBtn.className = 'nav-today';
    todayBtn.textContent = 'Сегодня';
    todayBtn.title = 'Перейти к сегодняшнему месяцу';
    todayBtn.setAttribute('aria-label', 'Сегодня');
    todayBtn.style.fontWeight = '600';
    todayBtn.style.fontSize = '0.85rem';
    todayBtn.style.width = 'auto';
    todayBtn.style.padding = '0 0.6rem';
    todayBtn.addEventListener('click', goToToday);

    const title = document.createElement('span');
    title.className = 'calendar-month-title';
    title.textContent = `${MONTH_NAMES[month - 1]} ${year}`;

    nav.appendChild(prevBtn);
    nav.appendChild(todayBtn);
    nav.appendChild(nextBtn);
    nav.appendChild(title);
}

function buildGrid(year, month) {
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

    const fdow = firstDayOfMonth(year, month);
    const dim = daysInMonth(year, month);
    const today = todayKey();

    const prevMonth = month === 1 ? 12 : month - 1;
    const prevYear = month === 1 ? year - 1 : year;
    const pdim = daysInMonth(prevYear, prevMonth);

    const nextMonth = month === 12 ? 1 : month + 1;
    const nextYear = month === 12 ? year + 1 : year;

    const totalCells = Math.ceil((fdow + dim) / 7) * 7;

    for (let i = 0; i < totalCells; i++) {
        const cell = document.createElement('div');
        cell.className = 'calendar-day-cell';

        let cellYear, cellMonth, cellDay, dateStr, isOtherMonth = false;

        if (i < fdow) {
            const day = pdim - fdow + 1 + i;
            cellYear = prevYear;
            cellMonth = prevMonth;
            cellDay = day;
            isOtherMonth = true;
        } else if (i >= fdow + dim) {
            const day = i - fdow - dim + 1;
            cellYear = nextYear;
            cellMonth = nextMonth;
            cellDay = day;
            isOtherMonth = true;
        } else {
            const day = i - fdow + 1;
            cellYear = year;
            cellMonth = month;
            cellDay = day;
        }

        dateStr = `${cellYear}-${String(cellMonth).padStart(2, '0')}-${String(cellDay).padStart(2, '0')}`;

        if (isOtherMonth) {
            cell.classList.add('other-month');
        }

        if (dateStr === today) {
            cell.classList.add('today');
        }

        if (!isOtherMonth && isOverdueDate(dateStr)) {
            cell.classList.add('overdue-day');
        }

        const numEl = document.createElement('span');
        numEl.className = 'calendar-day-number';
        numEl.textContent = cellDay;
        cell.appendChild(numEl);

        const tasksEl = document.createElement('div');
        tasksEl.className = 'calendar-day-tasks';
        tasksEl.dataset.date = dateStr;
        cell.appendChild(tasksEl);

        grid.appendChild(cell);
    }
}

function onCardRefresh(updatedTask) {
    const { year, month } = getCurrentMonth();
    updateTaskInState(year, month, updatedTask.id, (t) => {
        Object.assign(t, updatedTask);
    });
    const cardEl = document.querySelector(`.calendar-task-card[data-task-id="${updatedTask.id}"]`);
    if (cardEl) {
        updateCardInDOM(cardEl, updatedTask);
    } else {
        loadCalendar(year, month);
    }
}

function populateTasks(daysData) {
    const taskContainers = document.querySelectorAll('.calendar-day-tasks');
    let hasAnyTasks = false;

    for (const tc of taskContainers) {
        const dateKey = tc.dataset.date;
        const tasks = daysData[dateKey] || [];

        if (tasks.length === 0) {
            continue;
        }

        hasAnyTasks = true;
        const maxVisible = getMaxVisibleCards();
        const visible = tasks.slice(0, maxVisible);
        for (const task of visible) {
            const card = renderTaskCard(task, onCardRefresh);
            card._onCardRefresh = onCardRefresh;
            tc.appendChild(card);
        }

        if (tasks.length > maxVisible) {
            const more = document.createElement('div');
            more.className = 'calendar-more-count';
            more.textContent = `+${tasks.length - maxVisible} ещё`;
            tc.appendChild(more);
        }
    }

    if (!hasAnyTasks) {
        const grid = document.querySelector('.calendar-grid');
        if (grid) {
            const empty = document.createElement('div');
            empty.className = 'calendar-empty';
            empty.textContent = 'В этом месяце задач нет. Создайте шаблон в админке, чтобы начать.';
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
        const { year, month } = getCurrentMonth();
        loadCalendar(year, month);
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

async function loadCalendar(year, month) {
    showLoading();

    try {
        const data = await get(`/calendar?year=${year}&month=${month}`);

        setCurrentMonth(year, month);
        setUsers(data.users || []);

        const daysData = data.days || {};
        setCalendarTasks(`${year}-${month}`, daysData);

        renderNav(year, month);
        buildGrid(year, month);
        populateTasks(daysData);
        hideLoading();
    } catch (err) {
        hideLoading();
        const msg = err?.message || 'Не удалось подключиться к серверу';
        if (err.name === 'AbortError') return;
        showError(msg);
    }
}

function changeMonth(delta) {
    const { year, month } = getCurrentMonth();
    let m = month + delta;
    let y = year;
    if (m < 1) { m = 12; y--; }
    if (m > 12) { m = 1; y++; }
    setCurrentMonth(y, m);
    clearCalendarCache();
    closeAllDropdowns();
    loadCalendar(y, m);
}

function goToToday() {
    const d = new Date();
    clearCalendarCache();
    closeAllDropdowns();
    loadCalendar(d.getFullYear(), d.getMonth() + 1);
}

function init() {
    const { year, month } = getCurrentMonth();
    loadCalendar(year, month);
}

init();
