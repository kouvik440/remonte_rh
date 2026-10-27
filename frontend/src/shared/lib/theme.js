export const THEME_STORAGE_KEY = 'remonte-rh-theme';
const THEME_EVENT = 'remonte-rh-theme-change';

export function readTheme() {
  try {
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    if (stored === 'light' || stored === 'dark') return stored;
  } catch {
    // The theme remains usable when browser storage is unavailable.
  }
  return 'dark';
}

export function applyTheme(theme) {
  const selected = theme === 'light' ? 'light' : 'dark';
  document.documentElement.dataset.theme = selected;
  document.documentElement.classList.toggle('dark', selected === 'dark');
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', selected === 'dark' ? '#111111' : '#f5f6f7');
}

export function getTheme() {
  return document.documentElement.dataset.theme === 'light' ? 'light' : 'dark';
}

export function setTheme(theme) {
  applyTheme(theme);
  try { localStorage.setItem(THEME_STORAGE_KEY, getTheme()); } catch { /* Keep the in-memory choice. */ }
  window.dispatchEvent(new Event(THEME_EVENT));
}

export function subscribeTheme(onChange) {
  const onStorage = (event) => {
    if (event.key !== THEME_STORAGE_KEY && event.key !== null) return;
    applyTheme(readTheme());
    onChange();
  };
  window.addEventListener('storage', onStorage);
  window.addEventListener(THEME_EVENT, onChange);
  return () => {
    window.removeEventListener('storage', onStorage);
    window.removeEventListener(THEME_EVENT, onChange);
  };
}
