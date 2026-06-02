import { API_BASE } from './config.js';
import { showToast } from './ui/toast.js';

let currentAbortController = null;
const REQUEST_TIMEOUT = 10000;

async function request(path, options = {}) {
    const url = `${API_BASE}${path}`;

    if (currentAbortController) {
        currentAbortController.abort();
    }

    currentAbortController = new AbortController();

    const timer = setTimeout(() => {
        currentAbortController.abort();
    }, REQUEST_TIMEOUT);

    const opts = {
        headers: { 'Content-Type': 'application/json' },
        signal: currentAbortController.signal,
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
        if (err.name === 'AbortError') {
            clearTimeout(timer);
            throw err;
        }

        if (err instanceof Error) {
            showToast(err.message);
        }
        throw err;
    } finally {
        clearTimeout(timer);
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
