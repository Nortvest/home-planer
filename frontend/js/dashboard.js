import { setupTheme } from './theme.js';
import { get } from './api.js';
import { showToast } from './ui/toast.js';

const RECENT_LIMIT = 10;
const OVERDUE_LIMIT = 20;

function init() {
    setupTheme();
    loadDashboard();
}

async function loadDashboard() {
    const main = document.getElementById('app');
    if (!main) return;

    main.innerHTML = renderLoading();

    try {
        const data = await get('/dashboard');
        renderDashboard(main, data);
    } catch (err) {
        if (err.name !== 'AbortError') {
            renderNetworkError(main);
        }
    }
}

/* ---------- LOADING / ERROR ---------- */

function renderLoading() {
    return `<div class="loading-state" style="grid-column:1/-1;">Загрузка дашборда…</div>`;
}

function renderNetworkError(container) {
    container.innerHTML = `
        <div class="network-error">
            <p>Не удалось подключиться к серверу</p>
            <p style="font-size:0.8rem;color:var(--text-muted);margin-top:0.3rem;">Проверьте, что бэкенд запущен на указанном адресе</p>
            <button id="retry-btn">Повторить</button>
        </div>`;
    const btn = container.querySelector('#retry-btn');
    if (btn) {
        btn.addEventListener('click', loadDashboard);
    }
}

/* ---------- MAIN RENDER ---------- */

function renderDashboard(container, data) {
    const {
        balance_30d = [],
        balance_current_month = [],
        overdue = [],
        recent_done = [],
        summary = {},
    } = data;

    container.innerHTML = '';
    container.className = 'dashboard-grid';

    container.appendChild(createCard(renderSummary(summary), 'full-width', 'Сводка'));

    if (balance_current_month.length > 0) {
        container.appendChild(createCard(renderChart(balance_current_month), 'full-width', 'Баланс за месяц'));
    }

    container.appendChild(createCard(renderBalance(balance_30d, 'Баланс за 30 дней'), '', 'Баланс 30 дней'));
    container.appendChild(createCard(renderBalance(balance_current_month, 'Баланс за текущий месяц'), '', 'Баланс месяц'));
    container.appendChild(createCard(renderOverdue(overdue), '', 'Просрочено'));
    container.appendChild(createCard(renderRecentDone(recent_done), '', 'Последние выполненные'));
}

function createCard(innerHtml, extraClass, ariaLabel) {
    const wrapper = document.createElement('div');
    wrapper.className = `dash-card${extraClass ? ' ' + extraClass : ''}`;
    if (ariaLabel) wrapper.setAttribute('aria-label', ariaLabel);
    wrapper.innerHTML = innerHtml;
    return wrapper;
}

/* ---------- SUMMARY ---------- */

function renderSummary(summary) {
    const pending = summary.pending ?? 0;
    const overdue = summary.overdue ?? 0;
    const done = summary.done_this_month ?? 0;

    return `
        <h2>Сводка за месяц</h2>
        <div class="summary-stats">
            <div class="stat-item">
                <div>
                    <div class="stat-value pending">${pending}</div>
                    <div class="stat-label">Ожидает</div>
                </div>
            </div>
            <div class="stat-item">
                <div>
                    <div class="stat-value overdue">${overdue}</div>
                    <div class="stat-label">Просрочено</div>
                </div>
            </div>
            <div class="stat-item">
                <div>
                    <div class="stat-value done">${done}</div>
                    <div class="stat-label">Выполнено</div>
                </div>
            </div>
        </div>`;
}

/* ---------- BALANCE ---------- */

function renderBalance(items, title) {
    if (!items || items.length === 0) {
        return `<h2>${escHtml(title)}</h2><div class="empty-state">Нет данных</div>`;
    }

    let html = `<h2>${escHtml(title)}</h2>`;

    for (const item of items) {
        const user = item.user || {};
        const name = user.name || 'Без имени';
        const color = user.color || '#888';
        const spSum = item.sp_sum ?? 0;
        const tasksCount = item.tasks_count ?? 0;

        html += `
            <div class="balance-row">
                <div class="balance-color" style="background-color:${color}"></div>
                <div class="balance-info">
                    <div class="balance-name">${escHtml(name)}</div>
                    <div class="balance-detail">${tasksCount} задач</div>
                </div>
                <div class="balance-sp">${spSum} SP</div>
            </div>`;
    }

    return html;
}

/* ---------- CHART (SVG) ---------- */

function renderChart(items) {
    if (!items || items.length === 0) {
        return `<h2>Баланс за месяц</h2><div class="empty-state">Нет данных для графика</div>`;
    }

    const maxSp = Math.max(...items.map(i => i.sp_sum ?? 0), 1);
    const barWidth = Math.max(32, Math.min(80, 500 / items.length - 16));
    const chartH = 200;
    const padBottom = 40;
    const padLeft = 10;
    const padTop = 10;
    const totalW = items.length * (barWidth + 16) + padLeft + 10;
    const svgH = chartH + padBottom + padTop;

    const axisY = padTop;
    const axisBottom = padTop + chartH;

    let svg = `<div class="chart-container"><svg viewBox="0 0 ${totalW} ${svgH}" xmlns="http://www.w3.org/2000/svg">`;

    svg += `<line class="chart-axis" x1="${padLeft}" y1="${axisBottom}" x2="${totalW - 10}" y2="${axisBottom}" stroke-width="1"/>`;
    svg += `<text class="chart-max-label" x="${padLeft}" y="${axisY + 4}" font-size="11" text-anchor="middle">${maxSp}</text>`;
    svg += `<text class="chart-max-label" x="${padLeft}" y="${axisBottom + 20}" font-size="11" text-anchor="middle">0</text>`;

    items.forEach((item, i) => {
        const user = item.user || {};
        const name = user.name || '?';
        const color = user.color || '#888';
        const sp = item.sp_sum ?? 0;
        const barH = maxSp > 0 ? (sp / maxSp) * chartH : 0;
        const x = padLeft + i * (barWidth + 16) + 8;
        const y = axisBottom - barH;

        svg += `<rect x="${x}" y="${y}" width="${barWidth}" height="${Math.max(barH, 0)}" fill="${color}" rx="4"/>`;
        svg += `<text class="chart-val" x="${x + barWidth / 2}" y="${y - 4}" font-size="12" text-anchor="middle">${sp}</text>`;
        svg += `<text class="chart-label" x="${x + barWidth / 2}" y="${axisBottom + 20}" font-size="11" text-anchor="middle">${escHtml(name)}</text>`;
    });

    svg += `</svg></div>`;
    return svg;
}

/* ---------- OVERDUE ---------- */

function renderOverdue(tasks) {
    if (!tasks || tasks.length === 0) {
        return `<h2>Просрочено</h2><div class="empty-state">Нет просроченных задач — отлично!</div>`;
    }

    const sorted = [...tasks].sort((a, b) => (a.scheduled_date || '').localeCompare(b.scheduled_date || ''));
    const display = sorted.slice(0, OVERDUE_LIMIT);

    let html = `<h2>Просрочено (${tasks.length})</h2><ul class="task-list">`;
    for (const t of display) {
        const assignee = t.assignee || {};
        const color = assignee.color || '#888';
        html += `
            <li class="task-list-item overdue">
                <div class="task-list-color" style="background-color:${color}"></div>
                <span class="task-list-title">${escHtml(t.title || 'Без названия')}</span>
                <span class="task-list-meta">${formatDate(t.scheduled_date)}</span>
                <span class="task-list-sp">${t.sp_cost_current ?? 0} SP</span>
            </li>`;
    }
    html += '</ul>';

    if (tasks.length > OVERDUE_LIMIT) {
        html += `<div class="empty-state" style="padding:0.5rem 0 0;">ещё ${tasks.length - OVERDUE_LIMIT}…</div>`;
    }

    return html;
}

/* ---------- RECENT DONE ---------- */

function renderRecentDone(tasks) {
    if (!tasks || tasks.length === 0) {
        return `<h2>Последние выполненные</h2><div class="empty-state">Пока ничего не выполнено. Отметьте задачу как выполненную в календаре.</div>`;
    }

    const display = tasks.slice(0, RECENT_LIMIT);

    let html = `<h2>Последние выполненные (${tasks.length})</h2><ul class="task-list">`;
    for (const t of display) {
        const by = t.completed_by || {};
        const color = by.color || '#888';
        html += `
            <li class="task-list-item">
                <div class="task-list-color" style="background-color:${color}"></div>
                <span class="task-list-title" style="text-decoration:line-through;opacity:0.7">${escHtml(t.title || 'Без названия')}</span>
                <span class="task-list-meta">${escHtml(by.name || '?')} · ${formatDate(t.completed_at)}</span>
                <span class="task-list-sp">${t.sp_cost_at_completion ?? 0} SP</span>
            </li>`;
    }
    html += '</ul>';

    if (tasks.length > RECENT_LIMIT) {
        html += `<div class="empty-state" style="padding:0.5rem 0 0;">ещё ${tasks.length - RECENT_LIMIT}…</div>`;
    }

    return html;
}

/* ---------- UTILS ---------- */

function escHtml(str) {
    if (!str) return '';
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

function formatDate(dateStr) {
    if (!dateStr) return '—';
    const d = dateStr.replace('T', ' ').split('.')[0];
    const parts = d.split(' ');
    const datePart = parts[0];
    if (datePart && datePart.length === 10) {
        const [y, m, day] = datePart.split('-');
        return `${day}.${m}.${y}`;
    }
    return d;
}

init();
