import { setupTheme } from './theme.js';
import { get, post, patch, del } from './api.js';
import { setUsers } from './state.js';
import { showToast } from './ui/toast.js';

setupTheme();

const COLOR_PRESETS = [
    '#4f46e5', '#dc2626', '#16a34a', '#f59e0b',
    '#0891b2', '#c026d3', '#ea580c', '#2563eb',
    '#65a30d', '#7c3aed'
];

const RECURRENCE_OPTIONS = [
    { value: 'none', label: 'Нет (разовая)' },
    { value: 'daily', label: 'Ежедневно' },
    { value: 'weekly', label: 'Еженедельно' },
    { value: 'every_n_days', label: 'Каждые N дней' }
];

const WEEKDAYS = [
    'Воскресенье', 'Понедельник', 'Вторник', 'Среда',
    'Четверг', 'Пятница', 'Суббота'
];

let allUsers = [];
let allTemplates = [];
let currentTab = 'users';

/* ── Init ── */
document.addEventListener('DOMContentLoaded', async () => {
    renderAdminSkeleton();
    await loadAllData();
});

async function loadAllData() {
    try {
        const [usersRes] = await Promise.all([
            get('/users')
        ]);
        allUsers = usersRes.users || [];
        setUsers(allUsers);
        renderUsers();
    } catch (e) {
        showToast('Не удалось загрузить данные');
    }
}

async function loadTemplates() {
    try {
        const res = await get('/templates');
        allTemplates = res.templates || [];
        renderTemplates();
    } catch (e) {
        showToast('Не удалось загрузить шаблоны');
    }
}

/* ── Admin skeleton ── */
function renderAdminSkeleton() {
    const main = document.getElementById('app');
    main.innerHTML = `
        <div class="admin-container">
            <div class="admin-tabs">
                <button class="admin-tab-btn active" data-tab="users">Пользователи</button>
                <button class="admin-tab-btn" data-tab="templates">Шаблоны задач</button>
            </div>
            <div id="admin-users" class="admin-section active"></div>
            <div id="admin-templates" class="admin-section"></div>
        </div>
    `;

    main.querySelectorAll('.admin-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });

    switchTab('users');
}

function switchTab(tab) {
    currentTab = tab;
    document.querySelectorAll('.admin-tab-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.tab === tab);
    });
    document.querySelectorAll('.admin-section').forEach(s => {
        s.classList.remove('active');
    });
    const el = document.getElementById(`admin-${tab}`);
    if (el) el.classList.add('active');

    if (tab === 'templates' && allTemplates.length === 0) {
        loadTemplates();
    }
}

/* ══════════════════════════════════
   USERS
   ══════════════════════════════════ */
function renderUsers() {
    const container = document.getElementById('admin-users');
    if (!container) return;

    if (allUsers.length === 0) {
        container.innerHTML = `
            <div class="section-header">
                <h2 class="section-title">Пользователи</h2>
                <button class="btn btn-primary" id="btn-add-user">+ Добавить</button>
            </div>
            <div class="empty-state">Пользователи ещё не добавлены. Нажмите «Добавить».</div>
        `;
    } else {
        let html = `
            <div class="section-header">
                <h2 class="section-title">Пользователи</h2>
                <button class="btn btn-primary" id="btn-add-user">+ Добавить</button>
            </div>
            <div class="table-wrap">
                <table class="admin-table">
                    <thead>
                        <tr>
                            <th>Имя</th>
                            <th>Статус</th>
                            <th style="width:160px">Действия</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        allUsers.forEach(u => {
            const statusClass = u.active ? 'status-active' : 'status-inactive';
            const statusLabel = u.active ? 'Активный' : 'Неактивный';
            html += `
                <tr data-user-id="${u.id}">
                    <td>
                        <span class="user-color-dot" style="background-color:${u.color}"></span>
                        ${escHtml(u.name)}
                    </td>
                    <td><span class="status-badge ${statusClass}">${statusLabel}</span></td>
                    <td>
                        <div class="actions-cell">
                            <button class="btn btn-outline btn-sm btn-edit-user" data-user-id="${u.id}">Изменить</button>
                            ${u.active
                                ? `<button class="btn btn-outline btn-sm btn-deactivate-user" data-user-id="${u.id}">Деактивировать</button>`
                                : `<button class="btn btn-outline btn-sm btn-activate-user" data-user-id="${u.id}">Активировать</button>`
                            }
                            <button class="btn btn-danger btn-sm btn-delete-user" data-user-id="${u.id}">Удалить</button>
                        </div>
                    </td>
                </tr>
            `;
        });
        html += `</tbody></table></div>`;
        container.innerHTML = html;
    }

    container.querySelector('#btn-add-user')?.addEventListener('click', () => openUserForm());
    container.querySelectorAll('.btn-edit-user').forEach(b => {
        b.addEventListener('click', () => openUserForm(b.dataset.userId));
    });
    container.querySelectorAll('.btn-deactivate-user').forEach(b => {
        b.addEventListener('click', () => confirmDeactivateUser(b.dataset.userId));
    });
    container.querySelectorAll('.btn-activate-user').forEach(b => {
        b.addEventListener('click', async () => {
            try {
                await patch(`/users/${b.dataset.userId}`, { active: true });
                await refreshUsersOnly();
            } catch (e) {
                showToast(e.message || 'Ошибка активации');
            }
        });
    });
    container.querySelectorAll('.btn-delete-user').forEach(b => {
        b.addEventListener('click', () => confirmDeleteUser(b.dataset.userId));
    });
}

async function refreshUsersOnly() {
    try {
        const res = await get('/users');
        allUsers = res.users || [];
        setUsers(allUsers);
        renderUsers();
    } catch (e) {
        showToast('Ошибка обновления');
    }
}

function openUserForm(userId) {
    const user = userId ? allUsers.find(u => u.id === Number(userId)) : null;
    const isEdit = !!user;
    const name = user ? user.name : '';
    const color = user ? user.color : COLOR_PRESETS[0];

    const modal = createModal(isEdit ? 'Редактировать пользователя' : 'Новый пользователь');
    modal.innerHTML = `
        <div class="form-group">
            <label class="form-label" for="uf-name">Имя</label>
            <input class="form-input" type="text" id="uf-name" value="${escAttr(name)}" placeholder="Иван" required>
        </div>
        <div class="form-group">
            <label class="form-label">Цвет</label>
            <div class="color-picker-row">
                <div class="color-preview" id="uf-color-preview" style="background-color:${color}"></div>
                <div class="color-presets" id="uf-presets">
                    ${COLOR_PRESETS.map(c => `
                        <button type="button" class="color-preset-btn ${c === color ? 'selected' : ''}"
                                data-color="${c}" style="background-color:${c}"></button>
                    `).join('')}
                </div>
                <input type="text" class="form-input" id="uf-color" value="${color}"
                       style="width:100px;margin-left:auto" placeholder="#RRGGBB">
            </div>
        </div>
        <div id="uf-error" class="form-error"></div>
        <div class="modal-actions">
            <button class="btn btn-outline" id="uf-cancel">Отмена</button>
            <button class="btn btn-primary" id="uf-save">${isEdit ? 'Сохранить' : 'Создать'}</button>
        </div>
    `;

    const inputName = modal.querySelector('#uf-name');
    const inputColor = modal.querySelector('#uf-color');
    const preview = modal.querySelector('#uf-color-preview');
    const presetsContainer = modal.querySelector('#uf-presets');

    presetsContainer.addEventListener('click', (e) => {
        const btn = e.target.closest('.color-preset-btn');
        if (!btn) return;
        const c = btn.dataset.color;
        inputColor.value = c;
        preview.style.backgroundColor = c;
        presetsContainer.querySelectorAll('.color-preset-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
    });

    inputColor.addEventListener('input', () => {
        const v = inputColor.value.trim();
        if (/^#[0-9a-fA-F]{6}$/.test(v)) {
            preview.style.backgroundColor = v;
        }
        presetsContainer.querySelectorAll('.color-preset-btn').forEach(b => {
            b.classList.toggle('selected', b.dataset.color.toLowerCase() === v.toLowerCase());
        });
    });

    let submitted = false;
    modal.querySelector('#uf-save').addEventListener('click', async () => {
        if (submitted) return;
        submitted = true;
        const nameVal = inputName.value.trim();
        let colorVal = inputColor.value.trim();

        if (!nameVal) {
            modal.querySelector('#uf-error').textContent = 'Введите имя';
            return;
        }
        if (!/^#[0-9a-fA-F]{6}$/.test(colorVal)) {
            modal.querySelector('#uf-error').textContent = 'Неверный формат цвета (например #4f46e5)';
            return;
        }

        try {
            if (isEdit) {
                await patch(`/users/${userId}`, { name: nameVal, color: colorVal });
            } else {
                await post('/users', { name: nameVal, color: colorVal });
            }
            closeModal();
            await refreshUsersOnly();
        } catch (e) {
            const msg = e.message || 'Ошибка при сохранении';
            if (isEdit) {
                modal.querySelector('#uf-error').textContent = msg;
                submitted = false;
            } else {
                showToast(msg);
                closeModal();
            }
        }
    });

    modal.querySelector('#uf-cancel').addEventListener('click', closeModal);
}

async function confirmDeactivateUser(userId) {
    const user = allUsers.find(u => u.id === Number(userId));
    if (!user) return;

    const modal = createModalConfirm(`Деактивировать «${escHtml(user.name)}»?`);
    modal.querySelector('#confirm-ok').textContent = 'Деактивировать';

    let submitted = false;
    modal.querySelector('#confirm-ok').addEventListener('click', async () => {
        if (submitted) return;
        submitted = true;
        try {
            await patch(`/users/${userId}`, { active: false });
            closeModal();
            await refreshUsersOnly();
        } catch (e) {
            const msg = e.message || 'Ошибка';
            const errDiv = modal.querySelector('#confirm-error');
            if (errDiv) {
                errDiv.textContent = msg;
            } else {
                const errorEl = document.createElement('div');
                errorEl.id = 'confirm-error';
                errorEl.className = 'form-error';
                errorEl.textContent = msg;
                modal.querySelector('.modal-actions').before(errorEl);
            }
            submitted = false;
        }
    });

    modal.querySelector('#confirm-cancel').addEventListener('click', closeModal);
}

async function confirmDeleteUser(userId) {
    const user = allUsers.find(u => u.id === Number(userId));
    if (!user) return;

    const modal = createModalConfirm(`Удалить пользователя «${escHtml(user.name)}»? Это действие необратимо.`);
    modal.querySelector('#confirm-ok').textContent = 'Удалить';
    modal.querySelector('#confirm-ok').classList.add('btn-danger');

    let submitted = false;
    modal.querySelector('#confirm-ok').addEventListener('click', async () => {
        if (submitted) return;
        submitted = true;
        try {
            await del(`/users/${userId}`);
            closeModal();
            await refreshUsersOnly();
        } catch (e) {
            const msg = e.message || 'Ошибка при удалении';
            const errDiv = modal.querySelector('#confirm-error');
            if (errDiv) {
                errDiv.textContent = msg;
            } else {
                const errorEl = document.createElement('div');
                errorEl.id = 'confirm-error';
                errorEl.className = 'form-error';
                errorEl.textContent = msg;
                modal.querySelector('.modal-actions').before(errorEl);
            }
            submitted = false;
        }
    });

    modal.querySelector('#confirm-cancel').addEventListener('click', closeModal);
}

/* ══════════════════════════════════
   TEMPLATES
   ══════════════════════════════════ */
function renderTemplates() {
    const container = document.getElementById('admin-templates');
    if (!container) return;

    const activeUsers = allUsers.filter(u => u.active);

    if (allTemplates.length === 0) {
        container.innerHTML = `
            <div class="section-header">
                <h2 class="section-title">Шаблоны задач</h2>
                <button class="btn btn-primary" id="btn-add-template">+ Добавить</button>
            </div>
            <div class="empty-state">Шаблоны задач ещё не добавлены. Нажмите «Добавить».</div>
        `;
    } else {
        let html = `
            <div class="section-header">
                <h2 class="section-title">Шаблоны задач</h2>
                <button class="btn btn-primary" id="btn-add-template">+ Добавить</button>
            </div>
            <div class="table-wrap">
                <table class="admin-table">
                    <thead>
                        <tr>
                            <th>Название</th>
                            <th>SP</th>
                            <th>Повтор</th>
                            <th style="width:100px">По умолчанию</th>
                            <th>Статус</th>
                            <th style="width:160px">Действия</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        allTemplates.forEach(t => {
            const recLabel = getRecurrenceLabel(t.recurrence_type, t.recurrence_params);
            const assignee = activeUsers.find(u => u.id === t.default_assignee_id);
            const statusClass = t.active ? 'status-active' : 'status-inactive';
            const statusLabel = t.active ? 'Актив' : 'Неактив';

            html += `
                <tr data-template-id="${t.id}">
                    <td>${escHtml(t.title)}</td>
                    <td><span class="sp-badge">${t.sp_cost}</span></td>
                    <td><span class="recurrence-badge">${escHtml(recLabel)}</span></td>
                    <td>${assignee ? `${escHtml(assignee.name)}` : '—'}</td>
                    <td><span class="status-badge ${statusClass}">${statusLabel}</span></td>
                    <td>
                        <div class="actions-cell">
                            <button class="btn btn-outline btn-sm btn-edit-template" data-template-id="${t.id}">Изменить</button>
                            ${t.active
                                ? `<button class="btn btn-outline btn-sm btn-deactivate-template" data-template-id="${t.id}">Деакт.</button>`
                                : `<button class="btn btn-outline btn-sm btn-activate-template" data-template-id="${t.id}">Акт.</button>`
                            }
                            <button class="btn btn-danger btn-sm btn-delete-template" data-template-id="${t.id}">Удалить</button>
                        </div>
                    </td>
                </tr>
            `;
        });
        html += `</tbody></table></div>`;
        container.innerHTML = html;
    }

    container.querySelector('#btn-add-template')?.addEventListener('click', () => openTemplateForm());
    container.querySelectorAll('.btn-edit-template').forEach(b => {
        b.addEventListener('click', () => openTemplateForm(b.dataset.templateId));
    });
    container.querySelectorAll('.btn-deactivate-template').forEach(b => {
        b.addEventListener('click', () => confirmDeactivateTemplate(b.dataset.templateId));
    });
    container.querySelectorAll('.btn-activate-template').forEach(b => {
        b.addEventListener('click', async () => {
            try {
                await patch(`/templates/${b.dataset.templateId}`, { active: true });
                await loadTemplates();
            } catch (e) {
                showToast(e.message || 'Ошибка активации');
            }
        });
    });
    container.querySelectorAll('.btn-delete-template').forEach(b => {
        b.addEventListener('click', () => confirmDeleteTemplate(b.dataset.templateId));
    });
}

function getRecurrenceLabel(type, params) {
    switch (type) {
        case 'none': return 'Разовая';
        case 'daily': return 'Ежедневно';
        case 'weekly': {
            const d = params?.weekday ?? 0;
            return `${WEEKDAYS[d]}`;
        }
        case 'every_n_days': {
            const n = params?.interval_days ?? 1;
            return `Каждые ${n} дн.`;
        }
        default: return type || '—';
    }
}

function openTemplateForm(templateId) {
    const template = templateId ? allTemplates.find(t => t.id === Number(templateId)) : null;
    const isEdit = !!template;
    const activeUsers = allUsers.filter(u => u.active);

    const title = template ? template.title : '';
    const description = template ? (template.description || '') : '';
    const spCost = template ? template.sp_cost : 1;
    const recType = template ? template.recurrence_type : 'none';
    const recParams = template ? (template.recurrence_params || {}) : {};
    const defaultAssignee = template ? (template.default_assignee_id || '') : '';

    const modal = createModal(isEdit ? 'Редактировать шаблон' : 'Новый шаблон задачи');
    modal.innerHTML = `
        <div class="form-group">
            <label class="form-label" for="tf-title">Название</label>
            <input class="form-input" type="text" id="tf-title" value="${escAttr(title)}" placeholder="Помыть посуду" required>
        </div>
        <div class="form-group">
            <label class="form-label" for="tf-desc">Описание</label>
            <input class="form-input" type="text" id="tf-desc" value="${escAttr(description)}" placeholder="Необязательно">
        </div>
        <div class="form-group">
            <label class="form-label" for="tf-sp">SP (стоимость)</label>
            <input class="form-input" type="number" id="tf-sp" value="${spCost}" min="0">
        </div>
        <div class="form-group">
            <label class="form-label" for="tf-rec">Тип повторения</label>
            <select class="form-select" id="tf-rec">
                ${RECURRENCE_OPTIONS.map(o => `
                    <option value="${o.value}" ${recType === o.value ? 'selected' : ''}>${o.label}</option>
                `).join('')}
            </select>
        </div>
        <div class="recurrence-fields hidden" id="tf-rec-weekly">
            <label class="form-label" for="tf-weekday">День недели</label>
            <select class="form-select" id="tf-weekday">
                ${WEEKDAYS.map((w, i) => `
                    <option value="${i}" ${recParams.weekday === i ? 'selected' : ''}>${w}</option>
                `).join('')}
            </select>
        </div>
        <div class="recurrence-fields hidden" id="tf-rec-every">
            <label class="form-label" for="tf-interval">Каждые N дней</label>
            <input class="form-input" type="number" id="tf-interval" value="${recParams.interval_days || 7}" min="1">
        </div>
        <div class="form-group">
            <label class="form-label" for="tf-assignee">Исполнитель по умолчанию</label>
            <select class="form-select" id="tf-assignee">
                <option value="">— Не назначен —</option>
                ${activeUsers.map(u => `
                    <option value="${u.id}" ${String(defaultAssignee) === String(u.id) ? 'selected' : ''}>${escHtml(u.name)}</option>
                `).join('')}
            </select>
        </div>
        <div id="tf-error" class="form-error"></div>
        <div class="modal-actions">
            <button class="btn btn-outline" id="tf-cancel">Отмена</button>
            <button class="btn btn-primary" id="tf-save">${isEdit ? 'Сохранить' : 'Создать'}</button>
        </div>
    `;

    const recSelect = modal.querySelector('#tf-rec');
    const weeklyFields = modal.querySelector('#tf-rec-weekly');
    const everyFields = modal.querySelector('#tf-rec-every');
    const errorEl = modal.querySelector('#tf-error');

    function updateRecFields() {
        const v = recSelect.value;
        weeklyFields.classList.toggle('hidden', v !== 'weekly');
        everyFields.classList.toggle('hidden', v !== 'every_n_days');
    }
    updateRecFields();
    recSelect.addEventListener('change', updateRecFields);

    let submitted = false;
    modal.querySelector('#tf-save').addEventListener('click', async () => {
        if (submitted) return;
        submitted = true;
        errorEl.textContent = '';

        const titleVal = modal.querySelector('#tf-title').value.trim();
        const descVal = modal.querySelector('#tf-desc').value.trim() || null;
        const spVal = parseInt(modal.querySelector('#tf-sp').value, 10);
        const recVal = recSelect.value;
        let paramsVal = {};

        if (!titleVal) {
            errorEl.textContent = 'Введите название';
            submitted = false;
            return;
        }

        if (isNaN(spVal) || spVal < 0) {
            errorEl.textContent = 'SP должно быть числом ≥ 0';
            submitted = false;
            return;
        }

        if (recVal === 'weekly') {
            const wd = parseInt(modal.querySelector('#tf-weekday').value, 10);
            paramsVal = { weekday: wd };
        } else if (recVal === 'every_n_days') {
            const iv = parseInt(modal.querySelector('#tf-interval').value, 10);
            if (isNaN(iv) || iv < 1) {
                errorEl.textContent = 'Интервал должен быть ≥ 1';
                submitted = false;
                return;
            }
            paramsVal = { interval_days: iv };
        }

        const assigneeStr = modal.querySelector('#tf-assignee').value;
        const assigneeVal = assigneeStr ? parseInt(assigneeStr, 10) : null;

        const body = {
            title: titleVal,
            description: descVal,
            sp_cost: spVal,
            recurrence_type: recVal,
            recurrence_params: paramsVal,
            default_assignee_id: assigneeVal
        };

        try {
            if (isEdit) {
                await patch(`/templates/${templateId}`, body);
            } else {
                await post('/templates', body);
            }
            closeModal();
            await loadTemplates();
        } catch (e) {
            const msg = e.message || 'Ошибка при сохранении';
            if (isEdit) {
                errorEl.textContent = msg;
                submitted = false;
            } else {
                showToast(msg);
                closeModal();
            }
        }
    });

    modal.querySelector('#tf-cancel').addEventListener('click', closeModal);
}

async function confirmDeactivateTemplate(templateId) {
    const tpl = allTemplates.find(t => t.id === Number(templateId));
    if (!tpl) return;

    const modal = createModalConfirm(`Деактивировать шаблон «${escHtml(tpl.title)}»?`);
    modal.querySelector('#confirm-ok').textContent = 'Деактивировать';

    let submitted = false;
    modal.querySelector('#confirm-ok').addEventListener('click', async () => {
        if (submitted) return;
        submitted = true;
        try {
            await del(`/templates/${templateId}`);
            closeModal();
            await loadTemplates();
        } catch (e) {
            showToast(e.message || 'Ошибка');
            submitted = false;
        }
    });
    modal.querySelector('#confirm-cancel').addEventListener('click', closeModal);
}

async function confirmDeleteTemplate(templateId) {
    const tpl = allTemplates.find(t => t.id === Number(templateId));
    if (!tpl) return;

    const modal = createModalConfirm(`Удалить шаблон «${escHtml(tpl.title)}»?`);
    modal.querySelector('#confirm-ok').textContent = 'Удалить';
    modal.querySelector('#confirm-ok').classList.add('btn-danger');

    let submitted = false;
    modal.querySelector('#confirm-ok').addEventListener('click', async () => {
        if (submitted) return;
        submitted = true;
        try {
            await del(`/templates/${templateId}`);
            closeModal();
            await loadTemplates();
        } catch (e) {
            showToast(e.message || 'Ошибка');
            submitted = false;
        }
    });
    modal.querySelector('#confirm-cancel').addEventListener('click', closeModal);
}

/* ══════════════════════════════════
   Modal helpers
   ══════════════════════════════════ */
function createModal(title) {
    closeModal();
    const overlay = document.getElementById('modal-overlay');
    overlay.classList.remove('hidden');
    overlay.innerHTML = '';

    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `<div class="modal-title">${escHtml(title)}</div>`;
    overlay.appendChild(modal);

    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) closeModal();
    });

    const handler = (e) => {
        if (e.key === 'Escape') closeModal();
    };
    modal.dataset._escHandler = handler;
    document.addEventListener('keydown', handler);

    return modal;
}

function createModalConfirm(message) {
    const modal = createModal('Подтверждение');
    modal.classList.add('modal-confirm');
    modal.querySelector('.modal-title').textContent = 'Подтверждение';
    modal.querySelector('.modal-title').after(
        HTMLDivElement(() => `<p style="margin-bottom:0.5rem;font-size:0.9rem">${escHtml(message)}</p>`)
    );

    const errorDiv = document.createElement('div');
    errorDiv.id = 'confirm-error';
    errorDiv.className = 'form-error';
    const actionsDiv = document.createElement('div');
    actionsDiv.className = 'modal-actions';
    actionsDiv.innerHTML = `
        <button class="btn btn-outline" id="confirm-cancel">Отмена</button>
        <button class="btn btn-primary" id="confirm-ok">Подтвердить</button>
    `;

    modal.appendChild(errorDiv);
    modal.appendChild(actionsDiv);
    return modal;
}

function closeModal() {
    const overlay = document.getElementById('modal-overlay');
    const modal = overlay.querySelector('.modal');
    if (modal && modal.dataset._escHandler) {
        document.removeEventListener('keydown', modal.dataset._escHandler);
    }
    overlay.classList.add('hidden');
    overlay.innerHTML = '';
}

/* ══════════════════════════════════
   Utility
   ══════════════════════════════════ */
function escHtml(s) {
    if (!s) return '';
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function escAttr(s) {
    if (!s) return '';
    return s.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function HTMLDivElement(fn) {
    const d = document.createElement('div');
    d.innerHTML = fn();
    return d.firstElementChild || d;
}
