const STORAGE_KEY = 'planner-theme';

function getSystemTheme() {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function applyTheme(theme, shouldStore) {
    document.documentElement.setAttribute('data-theme', theme);
    if (shouldStore !== false) {
        localStorage.setItem(STORAGE_KEY, theme);
    }
}

export function setupTheme() {
    const stored = localStorage.getItem(STORAGE_KEY);
    const theme = stored || getSystemTheme();
    applyTheme(theme, false);

    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem(STORAGE_KEY)) {
            applyTheme(e.matches ? 'dark' : 'light', false);
        }
    });

    const btn = document.getElementById('theme-toggle');
    if (btn) {
        btn.addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            applyTheme(next, true);
        });
    }
}
