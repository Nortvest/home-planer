import { API_BASE } from './config.js';
import { showToast } from './ui/toast.js';

const REQUEST_TIMEOUT = 15000;

async function request(path, options = {}) {
    const url = `${API_BASE}${path}`;

    const controller = new AbortController();

    const timer = setTimeout(() => {
        controller.abort();
    }, REQUEST_TIMEOUT);

    const opts = {
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal,
        ...options,
    };

    if (opts.body && typeof opts.body === 'object') {
        opts.body = JSON.stringify(opts.body);
    }

    try {
        const response = await fetch(url, opts);

        if (!response.ok) {
            const data = await response.json().catch(() => null);
            const msg = data?.error?.message || `Ошибка ${response.status}: ${response.statusText}`;
            throw new Error(msg);
        }

        if (response.status === 204) {
            return null;
        }

        return await response.json();
    } catch (err) {
        clearTimeout(timer);

        if (err.name === 'AbortError') {
            throw err;
        }

        if (err instanceof TypeError && (err.message.includes('fetch') || err.message.includes('network') || err.message.includes('Failed'))){
            throw new Error('Сервер недоступен. Проверьте подключение и запущен ли бэкенд');
        }

        if (err instanceof Error) {
            showToast(err.message);
        }
        throw err;
    }
}

export function get(path) {
    return request(path, { method: 'GET' });
}

export function post(path, body) {
    return request(path, { method: 'POST', body });
}

export function patch(path, body) {
    return request(path, { method: 'PATCH', body });
}

export function del(path) {
    return request(path, { method: 'DELETE' });
}
