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
    setMonthOverview,
    getMonthOverview,
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
        updateMiniCalendarForCurrentMonth();
        return;
    }

    showLoading();

    try {
        const now = new Date();
        const [weekData, monthData] = await Promise.all([
            get(`/calendar/range?start=${start}&end=${end}`),
            get(`/calendar?year=${now.getFullYear()}&month=${now.getMonth() + 1}`)
        ]);

        setWeekStart(start);
        setLastLoadedWeek(start);
        setUsers(weekData.users || []);

        const daysData = weekData.days || {};
        setWeekTasks(start, daysData);

        const monthDays = monthData.days || {};
        setMonthOverview(now.getFullYear(), now.getMonth(), monthDays);

        const widget = document.querySelector('.mini-calendar-widget');
        if (widget) {
            widget.__daysData = monthDays;
            buildMiniCalendarContent(now.getFullYear(), now.getMonth(), monthDays, widget);
        }

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

let miniCalTooltipEl = null;
let miniCalTooltipTimer = null;

function getDaysInMonth(year, month) {
    return new Date(year, month + 1, 0).getDate();
}

function getFirstDowOfMonth(year, month) {
    const d = new Date(year, month, 1).getDay();
    return d === 0 ? 6 : d - 1;
}

function buildMiniCalendarContent(year, month, daysData, container) {
    container.innerHTML = '';

    const header = document.createElement('div');
    header.className = 'mini-cal-header';

    const prevBtn = document.createElement('button');
    prevBtn.className = 'mini-cal-nav-btn';
    prevBtn.textContent = '\u2039';
    prevBtn.title = 'Предыдущий месяц';
    prevBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const m = month === 0 ? 11 : month - 1;
        const y = month === 0 ? year - 1 : year;
        loadMonthOverview(y, m);
    });

    const title = document.createElement('span');
    title.className = 'mini-cal-title';
    title.textContent = `${MONTH_NAMES[month]} ${year}`;

    const nextMonth = month === 11 ? 0 : month + 1;
    const nextYear = month === 11 ? year + 1 : year;
    const now = new Date();
    const currentYear = now.getFullYear();
    const currentMonth = now.getMonth();
    const isFutureMonth = nextYear > currentYear || (nextYear === currentYear && nextMonth > currentMonth);

    const nextBtn = document.createElement('button');
    nextBtn.className = 'mini-cal-nav-btn';
    nextBtn.textContent = '\u203A';
    nextBtn.title = 'Следующий месяц';
    if (isFutureMonth) {
        nextBtn.disabled = true;
        nextBtn.style.opacity = '0.3';
        nextBtn.style.cursor = 'default';
    } else {
        nextBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            loadMonthOverview(nextYear, nextMonth);
        });
    }

    header.appendChild(prevBtn);
    header.appendChild(title);
    header.appendChild(nextBtn);
    container.appendChild(header);

    const grid = document.createElement('div');
    grid.className = 'mini-cal-grid';

    for (const name of ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']) {
        const hc = document.createElement('div');
        hc.className = 'mini-cal-header-cell';
        hc.textContent = name;
        grid.appendChild(hc);
    }

    const dow = getFirstDowOfMonth(year, month);
    const totalDays = getDaysInMonth(year, month);

    for (let i = 0; i < dow; i++) {
        const empty = document.createElement('div');
        empty.className = 'mini-cal-day empty';
        grid.appendChild(empty);
    }

    for (let d = 1; d <= totalDays; d++) {
        const dateObj = new Date(year, month, d);
        const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
        const tasks = (daysData && daysData[dateStr]) || [];
        const taskCount = tasks.length;

        const dayEl = document.createElement('div');
        dayEl.className = 'mini-cal-day';

        if (dateStr === todayStr()) {
            dayEl.classList.add('today');
        }

        const numEl = document.createElement('span');
        numEl.className = 'mini-cal-day-num';
        numEl.textContent = d;
        dayEl.appendChild(numEl);

        if (taskCount > 0) {
            const badge = document.createElement('span');
            badge.className = 'mini-cal-badge';
            badge.textContent = taskCount;
            dayEl.appendChild(badge);
        }

        dayEl.addEventListener('click', (e) => {
            e.stopPropagation();
            const weekStartForDate = getWeekStartForDate(dateStr);
            if (weekStartForDate > getCurrentWeekStart()) {
                showToast('Переход к будущим неделям недоступен', 'error');
                return;
            }
            closeMobileMiniCal();
            setWeekStart(weekStartForDate);
            clearCalendarCache();
            closeAllDropdowns();
            const end = addWeekDays(weekStartForDate, 1);
            loadWeek(weekStartForDate, end);
            updateMiniCalendarForCurrentMonth();
        });

        dayEl.addEventListener('mouseenter', () => {
            showMiniCalTooltip(dayEl, tasks);
        });

        dayEl.addEventListener('mouseleave', () => {
            hideMiniCalTooltip();
        });

        grid.appendChild(dayEl);
    }

    container.appendChild(grid);
}

function showMiniCalTooltip(el, tasks) {
    if (tasks.length === 0) return;

    hideMiniCalTooltip();

    miniCalTooltipEl = document.createElement('div');
    miniCalTooltipEl.className = 'mini-cal-tooltip';

    for (const task of tasks) {
        const line = document.createElement('div');
        line.className = 'mini-cal-tooltip-line';
        line.textContent = task.title;
        miniCalTooltipEl.appendChild(line);
    }

    const rect = el.getBoundingClientRect();
    miniCalTooltipEl.style.top = `${rect.bottom + 4}px`;
    miniCalTooltipEl.style.left = `${Math.min(rect.left, window.innerWidth - 220)}px`;
    document.body.appendChild(miniCalTooltipEl);
}

function hideMiniCalTooltip() {
    if (miniCalTooltipEl) {
        miniCalTooltipEl.remove();
        miniCalTooltipEl = null;
    }
}

function updateMiniCalendarForCurrentMonth() {
    const now = new Date();
    loadMonthOverview(now.getFullYear(), now.getMonth());
}

async function loadMonthOverview(year, month) {
    try {
        const data = await get(`/calendar?year=${year}&month=${month + 1}`);
        const daysData = data.days || {};
        setMonthOverview(year, month, daysData);

        const widget = document.querySelector('.mini-calendar-widget');
        if (widget) {
            buildMiniCalendarContent(year, month, daysData, widget);
            widget.__daysData = daysData;
        }

        if (window.__miniCalModalOpen) {
            const modalContent = document.querySelector('.mini-cal-modal-content');
            if (modalContent) {
                buildMiniCalendarContent(year, month, daysData, modalContent);
            }
        }
    } catch (err) {
        // Silent fail for background month overview load
    }
}

function initMiniCalendarDesktop() {
    const widget = document.createElement('div');
    widget.className = 'mini-calendar-widget';
    document.body.appendChild(widget);

    const now = new Date();
    loadMonthOverview(now.getFullYear(), now.getMonth());
}

function closeMobileMiniCal() {
    window.__miniCalModalOpen = false;
    const overlay = document.querySelector('.mini-cal-mobile-overlay');
    if (overlay) {
        overlay.remove();
    }
    hideMiniCalTooltip();
}

function openMobileMiniCal() {
    if (window.__miniCalModalOpen) return;
    window.__miniCalModalOpen = true;

    const overlay = document.createElement('div');
    overlay.className = 'mini-cal-mobile-overlay';

    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) closeMobileMiniCal();
    });

    document.addEventListener('keydown', function onEsc(e) {
        if (e.key === 'Escape') {
            document.removeEventListener('keydown', onEsc);
            closeMobileMiniCal();
        }
    });

    const modal = document.createElement('div');
    modal.className = 'mini-cal-modal';

    const closeBtn = document.createElement('button');
    closeBtn.className = 'mini-cal-modal-close';
    closeBtn.textContent = '\u00D7';
    closeBtn.title = 'Закрыть';
    closeBtn.addEventListener('click', closeMobileMiniCal);
    modal.appendChild(closeBtn);

    const content = document.createElement('div');
    content.className = 'mini-cal-modal-content';
    modal.appendChild(content);
    overlay.appendChild(modal);
    document.body.appendChild(overlay);

    const overview = getMonthOverview();
    if (overview.year !== null && overview.month !== null) {
        buildMiniCalendarContent(overview.year, overview.month, overview.days, content);
    } else {
        const now = new Date();
        loadMonthOverview(now.getFullYear(), now.getMonth());
        const ov = getMonthOverview();
        buildMiniCalendarContent(ov.year, ov.month, ov.days, content);
    }
}

function initMiniCalendar() {
    const toggle = document.getElementById('mini-cal-toggle');
    if (toggle) {
        toggle.addEventListener('click', openMobileMiniCal);
    }

    if (window.matchMedia('(min-width: 601px)').matches) {
        initMiniCalendarDesktop();
    }
}

function init() {
    const currentWeekStart = getCurrentWeekStart();
    setWeekStart(currentWeekStart);
    const { start, end } = getWeekRange();
    loadWeek(start, end);
    initMiniCalendar();
}

init();
