import { post } from './api.js';
import {
    getUsers,
    updateTaskInState,
    getCurrentMonth,
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
        default: return '';
    }
}

function renderTaskCard(task, onCardRefresh) {
    const card = document.createElement('div');
    card.className = 'calendar-task-card';
    card.dataset.taskId = task.id;

    if (task.status === 'done') {
        card.classList.add('done');
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
    card.appendChild(dropdown);

    if (task.status !== 'done') {
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

function buildDropdownItems(dropdown, task, onCardRefresh) {
    const users = getUsers();

    const completeItem = document.createElement('button');
    completeItem.className = 'card-dropdown-item';
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
        const showSub = () => {
            if (!dropdown.classList.contains('open')) return;
            submenu.classList.add('open');
        };
        const hideSub = () => {
            submenu.classList.remove('open');
        };

        reassignItem.addEventListener('mouseenter', showSub);
        reassignItem.addEventListener('click', (e) => {
            e.stopPropagation();
            if (submenu.classList.contains('open')) {
                hideSub();
            } else {
                showSub();
            }
        });

        dropdown.addEventListener('mouseleave', hideSub);
    }

    dropdown.appendChild(createSeparator());

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

function openTaskDetails(taskId, _onCardRefresh) {
    closeAllDropdowns();
}

function toggleDropdown(card, dropdown) {
    if (dropdown.classList.contains('open')) {
        closeAllDropdowns();
        return;
    }
    closeAllDropdowns();
    dropdown.classList.add('open');
    activeDropdownEl = dropdown;
    card._dropdown = dropdown;
}

function closeAllDropdowns() {
    if (activeDropdownEl) {
        activeDropdownEl.classList.remove('open');
        const submenus = activeDropdownEl.querySelectorAll('.card-reassign-submenu');
        submenus.forEach(s => s.classList.remove('open'));
        activeDropdownEl = null;
    }
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

    if (updatedTask.status !== 'done') {
        const dropdown = document.createElement('div');
        dropdown.className = 'card-dropdown';
        dropdown.setAttribute('role', 'menu');
        buildDropdownItems(dropdown, updatedTask, card._onCardRefresh);
        card.appendChild(dropdown);

        actionsBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleDropdown(card, dropdown);
        });
    }
}

document.addEventListener('click', (e) => {
    if (activeDropdownEl && !e.target.closest('.card-dropdown') && !e.target.closest('.card-actions-btn')) {
        closeAllDropdowns();
    }
});

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeAllDropdowns();
    }
});

export { renderTaskCard, updateCardInDOM, closeAllDropdowns };