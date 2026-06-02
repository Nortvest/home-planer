const DURATION = 5000;

let toastTimer = null;

export function showToast(message, type) {
    let toast = document.getElementById('error-toast');
    if (!toast) return;

    toast.textContent = message;
    toast.className = 'toast';

    if (type === 'success') {
        toast.style.backgroundColor = 'var(--toast-bg)';
    } else {
        toast.style.backgroundColor = 'var(--toast-error-bg)';
    }

    toast.classList.remove('hidden');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
        toast.classList.add('hidden');
    }, DURATION);
}
