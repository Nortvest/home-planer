let API_BASE = 'API_BASE_PLACEHOLDER';

if (window.__CONFIG__?.apiBase) {
    API_BASE = window.__CONFIG__.apiBase;
} else {
    const body = document.querySelector('body');
    const attr = body?.getAttribute('data-api-base');
    if (attr) {
        API_BASE = attr;
    }
}

export { API_BASE };
