import { post, get } from './api.js';
import {
    getUsers,
} from './state.js';

let activeDropdownEl = null;
let longPressTimer = null;
const LONG_PRESS_DELAY = 500;

function getUserColor(user) {
    return user?.color || '#999999';
}

function getStatusIcon(status) {
    switch (status) {
        case 'done': return '✓';
        case 'overdue': return '!';
        case 'cancelled': return '✕';
        default: return '';
    }
}

function renderTaskCard(task, onCardRefresh) {
    const card = document.createElement('div');
    card.className = 'calendar-task-card';
    card.dataset.taskId = task.id;

    if (task.status === 'done') {
        card.classList.add('done');
    } else if (task.status === 'cancelled') {
        card.classList.add('cancelled');
    } else if (task.status === 'overdue') {
        card.classList.add('overdue');
    }

    const assignee = task.assignee;
    const color = assignee ? getUserColor(assignee) : '#999999';

    const bar = document.createElement('div');
    bar.className = 'calendar-task-color-bar';
    bar.style.backgroundColor = color;
    card.appendChild(bar);

    const inner = document.createElement('div');
    inner.className = 'calendar-task-card-inner';

    const header = document.createElement('div');
    header.className = 'calendar-task-header';

    const icon = document.createElement('span');
    icon.className = 'card-status-icon';
    icon.textContent = getStatusIcon(task.status);
    header.appendChild(icon);

    const title = document.createElement('div');
    title.className = 'calendar-task-title';
    title.textContent = task.title;
    header.appendChild(title);

    const sp = document.createElement('span');
    sp.className = 'calendar-task-sp';
    const spVal = task.sp_cost_current ?? task.sp_cost_at_completion ?? 0;
    sp.textContent = `SP ${spVal}`;
    header.appendChild(sp);

    inner.appendChild(header);
    card.appendChild(inner);

    const actionsBtn = document.createElement('button');
    actionsBtn.className = 'card-actions-btn';
    actionsBtn.textContent = '⋮';
    actionsBtn.title = 'Действия';
    actionsBtn.setAttribute('aria-label', 'Действия с задачей');
    actionsBtn.setAttribute('aria-haspopup', 'true');
    card.appendChild(actionsBtn);

    const dropdown = document.createElement('div');
    dropdown.className = 'card-dropdown';
    dropdown.setAttribute('role', 'menu');
    dropdown._resetPosition = () => {
        dropdown.style.position = '';
        dropdown.style.top = '';
        dropdown.style.left = '';
        dropdown.style.zIndex = '';
    };
    card._dropdown = dropdown;

    if (task.status === 'done') {
        buildDoneDropdownItems(dropdown, task, onCardRefresh);
    } else if (task.status === 'cancelled') {
        buildCancelledDropdownItems(dropdown, task, onCardRefresh);
    } else {
        buildDropdownItems(dropdown, task, onCardRefresh);
    }

    actionsBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleDropdown(card, dropdown);
    });

    setupLongPress(card, actionsBtn, (e) => {
        e.stopPropagation();
        toggleDropdown(card, dropdown);
    });

    return card;
}

function buildDoneDropdownForRefresh(card, actionsBtn, task) {
    const existingDropdown = card.querySelector('.card-dropdown');
    if (existingDropdown) {
        existingDropdown.remove();
    }
    const dropdown = document.createElement('div');
    dropdown.className = 'card-dropdown';
    dropdown.setAttribute('role', 'menu');
    dropdown._resetPosition = () => {
        dropdown.style.position = '';
        dropdown.style.top = '';
        dropdown.style.left = '';
        dropdown.style.zIndex = '';
    };
    buildDoneDropdownItems(dropdown, task, card._onCardRefresh);
    card._dropdown = dropdown;

    actionsBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleDropdown(card, dropdown);
    });
}

function buildCancelledDropdownItems(dropdown, task, onCardRefresh) {
    const restoreItem = document.createElement('button');
    restoreItem.className = 'card-dropdown-item';
    restoreItem.textContent = 'Вернуть задачу';
    restoreItem.setAttribute('role', 'menuitem');
    restoreItem.addEventListener('click', (e) => {
        e.stopPropagation();
        restoreTask(task.id, onCardRefresh);
        closeAllDropdowns();
    });
    dropdown.appendChild(restoreItem);

    const detailItem = document.createElement('button');
    detailItem.className = 'card-dropdown-item';
    detailItem.textContent = 'Открыть детали';
    detailItem.setAttribute('role', 'menuitem');
    detailItem.addEventListener('click', (e) => {
        e.stopPropagation();
        openTaskDetails(task.id, onCardRefresh);
    });
    dropdown.appendChild(detailItem);
}

function buildDoneDropdownItems(dropdown, task, onCardRefresh) {
    const detailItem = document.createElement('button');
    detailItem.className = 'card-dropdown-item';
    detailItem.textContent = 'Открыть детали';
    detailItem.setAttribute('role', 'menuitem');
    detailItem.addEventListener('click', (e) => {
        e.stopPropagation();
        openTaskDetails(task.id, onCardRefresh);
    });
    dropdown.appendChild(detailItem);

    const uncompleteItem = document.createElement('button');
    uncompleteItem.className = 'card-dropdown-item danger';
    uncompleteItem.textContent = 'Отменить выполнение';
    uncompleteItem.setAttribute('role', 'menuitem');
    uncompleteItem.addEventListener('click', (e) => {
        e.stopPropagation();
        uncompleteTask(task.id, onCardRefresh);
        closeAllDropdowns();
    });
    dropdown.appendChild(uncompleteItem);
}

function buildDropdownItems(dropdown, task, onCardRefresh) {
    const users = getUsers();

    const completeItem = document.createElement('button');
    completeItem.className = 'card-dropdown-item success';
    completeItem.textContent = 'Отметить выполненной';
    completeItem.setAttribute('role', 'menuitem');
    completeItem.addEventListener('click', (e) => {
        e.stopPropagation();
        const completedById = task.assignee?.id || users[0]?.id;
        completeTask(task.id, completedById, onCardRefresh);
    });
    dropdown.appendChild(completeItem);

    dropdown.appendChild(createSeparator());

    const reassignItem = document.createElement('button');
    reassignItem.className = 'card-dropdown-item';
    reassignItem.textContent = 'Переназначить на…';
    reassignItem.setAttribute('role', 'menuitem');
    dropdown.appendChild(reassignItem);

    const submenu = document.createElement('div');
    submenu.className = 'card-reassign-submenu';
    submenu.setAttribute('role', 'menu');
    dropdown.appendChild(submenu);

    for (const user of users) {
        if (user.id === task.assignee?.id) continue;

        const subItem = document.createElement('button');
        subItem.className = 'card-dropdown-item';
        subItem.setAttribute('role', 'menuitem');

        const dot = document.createElement('span');
        dot.className = 'card-reassign-user-color';
        dot.style.backgroundColor = user.color;
        subItem.appendChild(dot);

        const name = document.createElement('span');
        name.textContent = user.name;
        subItem.appendChild(name);

        subItem.addEventListener('click', (e) => {
            e.stopPropagation();
            reassignTask(task.id, user.id, onCardRefresh);
        });

        submenu.appendChild(subItem);
    }

    if (users.length > 1) {
        let subHideTimer = null;

        let subMeasuredWidth = null;
        const showSub = () => {
            if (!dropdown.classList.contains('open')) return;
            clearTimeout(subHideTimer);
            const rect = reassignItem.getBoundingClientRect();
            if (!subMeasuredWidth) {
                submenu.style.visibility = 'hidden';
                submenu.style.display = 'block';
                submenu.style.position = 'fixed';
                submenu.style.top = '0';
                submenu.style.left = '0';
                subMeasuredWidth = submenu.offsetWidth;
                submenu.style.visibility = '';
                submenu.style.display = '';
                submenu.style.position = '';
                submenu.style.top = '';
                submenu.style.left = '';
            }
            submenu.classList.add('open');
            submenu.style.position = 'fixed';
            submenu.style.top = `${rect.top}px`;
            submenu.style.left = `${rect.left - subMeasuredWidth}px`;
            submenu.style.zIndex = '10000';
        };
        const hideSub = () => {
            subHideTimer = setTimeout(() => {
                subHideTimer = null;
                clearSubmenuStyles(submenu);
            }, 100);
        };

        reassignItem.addEventListener('mouseenter', () => {
            if (dropdown.classList.contains('open')) showSub();
        });
        reassignItem.addEventListener('click', (e) => {
            e.stopPropagation();
            if (submenu.classList.contains('open')) {
                hideSub();
            } else {
                showSub();
            }
        });

        submenu.addEventListener('mouseenter', () => {
            clearTimeout(subHideTimer);
        });
        submenu.addEventListener('mouseleave', hideSub);
    }

    dropdown.appendChild(createSeparator());

    const cancelItem = document.createElement('button');
    cancelItem.className = 'card-dropdown-item';
    cancelItem.textContent = 'Отменить задачу';
    cancelItem.setAttribute('role', 'menuitem');
    cancelItem.addEventListener('click', (e) => {
        e.stopPropagation();
        cancelTask(task.id, onCardRefresh);
        closeAllDropdowns();
    });
    dropdown.appendChild(cancelItem);

    const detailItem = document.createElement('button');
    detailItem.className = 'card-dropdown-item';
    detailItem.textContent = 'Открыть детали';
    detailItem.setAttribute('role', 'menuitem');
    detailItem.addEventListener('click', (e) => {
        e.stopPropagation();
        openTaskDetails(task.id, onCardRefresh);
    });
    dropdown.appendChild(detailItem);
}

function createSeparator() {
    const sep = document.createElement('div');
    sep.className = 'card-dropdown-separator';
    return sep;
}

async function completeTask(taskId, completedById, onCardRefresh) {
    try {
        const updated = await post(`/instances/${taskId}/complete`, {
            completed_by_id: completedById,
        });
        closeAllDropdowns();
        if (updated && onCardRefresh) {
            onCardRefresh(updated);
        }
    } catch {
        // error toast handled by api.js
    }
}

async function reassignTask(taskId, toUserId, onCardRefresh) {
    try {
        const updated = await post(`/instances/${taskId}/reassign`, {
            to_user_id: toUserId,
        });
        closeAllDropdowns();
        if (updated && onCardRefresh) {
            onCardRefresh(updated);
        }
    } catch {
        // error toast handled by api.js
    }
}

async function cancelTask(taskId, onCardRefresh) {
    try {
        const updated = await post(`/instances/${taskId}/cancel`);
        closeAllDropdowns();
        if (updated && onCardRefresh) {
            onCardRefresh(updated);
        }
    } catch {
        // error toast handled by api.js
    }
}

async function restoreTask(taskId, onCardRefresh) {
    try {
        const updated = await post(`/instances/${taskId}/restore`);
        closeAllDropdowns();
        if (updated && onCardRefresh) {
            onCardRefresh(updated);
        }
    } catch {
        // error toast handled by api.js
    }
}

function openTaskDetails(taskId, onCardRefresh) {
    closeAllDropdowns();
    fetchTaskDetails(taskId, onCardRefresh);
}

async function fetchTaskDetails(taskId, onCardRefresh) {
    try {
        const task = await get(`/instances/${taskId}`);
        if (task) {
            showDetailsModal(task, onCardRefresh);
        }
    } catch {
        // error handled by api.js
    }
}

function showDetailsModal(task, onCardRefresh) {
    const overlay = document.createElement('div');
    overlay.className = 'task-details-overlay';
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) closeModal(overlay);
    });

    const modal = document.createElement('div');
    modal.className = 'task-details-modal';

    const header = document.createElement('div');
    header.className = 'task-details-header';
    const titleEl = document.createElement('h3');
    titleEl.textContent = task.title;
    header.appendChild(titleEl);
    const closeBtn = document.createElement('button');
    closeBtn.className = 'task-details-close';
    closeBtn.textContent = '✕';
    closeBtn.title = 'Закрыть';
    closeBtn.setAttribute('aria-label', 'Закрыть');
    closeBtn.addEventListener('click', () => closeModal(overlay));
    header.appendChild(closeBtn);
    modal.appendChild(header);

    const body = document.createElement('div');
    body.className = 'task-details-body';

    const rows = [
        ['Дата', formatDate(task.scheduled_date)],
        ['Исполнитель', task.assignee ? task.assignee.name : '—'],
        ['Статус', [getStatusLabel(task.status), `status-badge status-${task.status}`]],
        ['Стоимость', `${task.sp_cost_current ?? 0} SP`],
        ['Выполнено', task.completed_at ? formatDate(task.completed_at.split('T')[0]) : '—'],
        ['Выполнил', task.completed_by ? task.completed_by.name : '—'],
    ];

    if (task.transfers && task.transfers.length > 0) {
        const transferTexts = task.transfers.map(t => {
            const from = t.from_user ? t.from_user.name : '?';
            const to = t.to_user ? t.to_user.name : '?';
            return `${from} → ${to} (${formatDate(t.transferred_at.split('T')[0])})`;
        });
        rows.push(['Переназначения', transferTexts.join('; ')]);
    }

    for (const [label, value] of rows) {
        const row = document.createElement('div');
        row.className = 'task-details-row';
        const labelEl = document.createElement('span');
        labelEl.className = 'task-details-row-label';
        labelEl.textContent = label;
        const valEl = document.createElement('span');
        valEl.className = 'task-details-row-value';
        if (Array.isArray(value)) {
            const badge = document.createElement('span');
            badge.className = value[1];
            badge.textContent = value[0];
            valEl.appendChild(badge);
        } else {
            valEl.textContent = value;
        }
        row.appendChild(labelEl);
        row.appendChild(valEl);
        body.appendChild(row);
    }
    modal.appendChild(body);

    const footer = document.createElement('div');
    footer.className = 'task-details-footer';

    if (task.status === 'done') {
        const uncompleteBtn = document.createElement('button');
        uncompleteBtn.className = 'task-details-btn uncomplete';
        uncompleteBtn.textContent = 'Отменить выполнение';
        uncompleteBtn.addEventListener('click', () => {
            uncompleteTask(task.id, onCardRefresh);
        });
        footer.appendChild(uncompleteBtn);
    }

    modal.appendChild(footer);
    overlay.appendChild(modal);
    document.body.appendChild(overlay);
}

function getStatusLabel(status) {
    switch (status) {
        case 'done': return 'Выполнено';
        case 'overdue': return 'Просрочено';
        case 'pending': return 'Ожидает';
        case 'cancelled': return 'Отменено';
        default: return status;
    }
}

function formatDate(dateStr) {
    if (!dateStr) return '—';
    const parts = dateStr.split('-');
    if (parts.length === 3) {
        return `${parts[2]}.${parts[1]}.${parts[0]}`;
    }
    return dateStr;
}

function closeModal(overlay) {
    if (overlay.parentNode) {
        overlay.parentNode.removeChild(overlay);
    }
}

async function uncompleteTask(taskId, onCardRefresh) {
    try {
        const updated = await post(`/instances/${taskId}/uncomplete`);
        const overlay = document.querySelector('.task-details-overlay');
        if (overlay) closeModal(overlay);
        if (updated && onCardRefresh) {
            onCardRefresh(updated);
        }
    } catch {
        // error handled by api.js
    }
}

function toggleDropdown(card, dropdown) {
    if (dropdown.classList.contains('open')) {
        closeAllDropdowns();
        return;
    }
    closeAllDropdowns();
    document.body.appendChild(dropdown);
    positionDropdown(card, dropdown);
    dropdown.classList.add('open');
    activeDropdownEl = dropdown;
}

function positionDropdown(card, dropdown) {
    const rect = card.getBoundingClientRect();
    dropdown.style.display = 'block';
    const w = dropdown.offsetWidth;
    dropdown.style.position = 'fixed';
    dropdown.style.top = `${rect.bottom}px`;
    dropdown.style.left = `${rect.right - w}px`;
    dropdown.style.zIndex = '9999';
}

function closeAllDropdowns() {
    if (activeDropdownEl) {
        activeDropdownEl.classList.remove('open');
        const submenus = activeDropdownEl.querySelectorAll('.card-reassign-submenu');
        submenus.forEach(s => clearSubmenuStyles(s));
        if (activeDropdownEl.parentNode) {
            activeDropdownEl.parentNode.removeChild(activeDropdownEl);
        }
        activeDropdownEl._resetPosition();
        activeDropdownEl = null;
    }
}

function clearSubmenuStyles(el) {
    el.classList.remove('open');
    el.style.position = '';
    el.style.top = '';
    el.style.left = '';
    el.style.zIndex = '';
}

function setupLongPress(card, btn, handler) {
    card.addEventListener('touchstart', (e) => {
        longPressTimer = setTimeout(() => {
            longPressTimer = null;
            handler(e);
        }, LONG_PRESS_DELAY);
    }, { passive: true });

    card.addEventListener('touchend', () => {
        if (longPressTimer) {
            clearTimeout(longPressTimer);
            longPressTimer = null;
        }
    });

    card.addEventListener('touchmove', () => {
        if (longPressTimer) {
            clearTimeout(longPressTimer);
            longPressTimer = null;
        }
    });
}

function updateCardInDOM(taskEl, updatedTask) {
    const card = taskEl.closest('.calendar-task-card');
    if (!card) return;

    card.className = 'calendar-task-card';
    if (updatedTask.status === 'done') {
        card.classList.add('done');
    } else if (updatedTask.status === 'cancelled') {
        card.classList.add('cancelled');
    } else if (updatedTask.status === 'overdue') {
        card.classList.add('overdue');
    }

    const bar = card.querySelector('.calendar-task-color-bar');
    if (bar && updatedTask.assignee) {
        bar.style.backgroundColor = getUserColor(updatedTask.assignee);
    }

    const title = card.querySelector('.calendar-task-title');
    if (title) {
        title.textContent = updatedTask.title;
    }

    const sp = card.querySelector('.calendar-task-sp');
    if (sp) {
        const spVal = updatedTask.sp_cost_current ?? updatedTask.sp_cost_at_completion ?? 0;
        sp.textContent = `SP ${spVal}`;
    }

    const icon = card.querySelector('.card-status-icon');
    if (icon) {
        icon.textContent = getStatusIcon(updatedTask.status);
    }

    const actionsBtn = card.querySelector('.card-actions-btn');
    if (actionsBtn) {
        actionsBtn.style.display = '';
    }

    const existingDropdown = card.querySelector('.card-dropdown');
    if (existingDropdown) {
        existingDropdown.remove();
    }

    if (updatedTask.status === 'cancelled') {
        const existingDropdown2 = card.querySelector('.card-dropdown');
        if (existingDropdown2) {
            existingDropdown2.remove();
        }
        const dropdown2 = document.createElement('div');
        dropdown2.className = 'card-dropdown';
        dropdown2.setAttribute('role', 'menu');
        dropdown2._resetPosition = () => {
            dropdown2.style.position = '';
            dropdown2.style.top = '';
            dropdown2.style.left = '';
            dropdown2.style.zIndex = '';
        };
        buildCancelledDropdownItems(dropdown2, updatedTask, card._onCardRefresh);
        card._dropdown = dropdown2;
        actionsBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleDropdown(card, dropdown2);
        });
    } else if (updatedTask.status !== 'done') {
        const dropdown = document.createElement('div');
        dropdown.className = 'card-dropdown';
        dropdown.setAttribute('role', 'menu');
        dropdown._resetPosition = () => {
            dropdown.style.position = '';
            dropdown.style.top = '';
            dropdown.style.left = '';
            dropdown.style.zIndex = '';
        };
        buildDropdownItems(dropdown, updatedTask, card._onCardRefresh);
        card._dropdown = dropdown;

        actionsBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleDropdown(card, dropdown);
        });
    } else {
        buildDoneDropdownForRefresh(card, actionsBtn, updatedTask);
    }
}

document.addEventListener('click', (e) => {
    if (activeDropdownEl && !e.target.closest('.card-dropdown') && !e.target.closest('.card-actions-btn') && !e.target.closest('.card-reassign-submenu')) {
        closeAllDropdowns();
    }
});

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeAllDropdowns();
    }
});

export { renderTaskCard, updateCardInDOM, closeAllDropdowns };