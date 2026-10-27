import { navigate } from './navigation.js';
const apiBase = (import.meta.env?.VITE_API_BASE_URL || '').trim().replace(/\/+$/, '');

export const getUser = () => {
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    return user && typeof user === 'object' && !Array.isArray(user) ? user : {};
  } catch { return {}; }
};

export const hasPermission = (code) => {
  const permissions = getUser().permissions;
  return Array.isArray(permissions) && permissions.includes(code);
};

export const clearSession = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
};

let pendingRefresh = null;
const pendingReads = new Map();

const requestNewToken = async () => {
  const refresh = localStorage.getItem('refresh_token');
  if (!refresh) throw new Error('Votre session a expiré. Reconnectez-vous.');
  const response = await fetch(`${apiBase}/api/auth/refresh/`, {
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok || !data.access) throw new Error('Votre session a expiré. Reconnectez-vous.');
  localStorage.setItem('access_token', data.access);
  if (data.refresh) localStorage.setItem('refresh_token', data.refresh);
  return data.access;
};

const refreshToken = () => {
  if (!pendingRefresh) {
    pendingRefresh = requestNewToken().finally(() => { pendingRefresh = null; });
  }
  return pendingRefresh;
};

const sendApiRequest = async (path, options, retried) => {
  const { responseType, ...requestOptions } = options;
  const accessToken = localStorage.getItem('access_token');
  const headers = {
    Accept: 'application/json',
    ...(options.headers || {}),
    ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
  };
  let response = await fetch(`${apiBase}${path}`, { ...requestOptions, headers });
  if (response.status === 401 && !retried && localStorage.getItem('refresh_token')) {
    try {
      const currentToken = localStorage.getItem('access_token');
      const token = currentToken && currentToken !== accessToken ? currentToken : await refreshToken();
      response = await fetch(`${apiBase}${path}`, {
        ...requestOptions,
        headers: { ...headers, Authorization: `Bearer ${token}` },
      });
    } catch (error) {
      clearSession();
      navigate('/connexion?session=expired', { replace: true });
      throw error;
    }
  }
  const contentType = response.headers.get('content-type') || '';
  if (response.ok && responseType === 'blob') return response.blob();
  const data = response.status === 204
    ? null
    : contentType.includes('application/json')
      ? await response.json().catch(() => ({}))
      : await response.text();
  if (!response.ok) {
    const message = formatApiError(data);
    const error = new Error(message);
    error.status = response.status;
    error.details = data;
    throw error;
  }
  return data;
};

export const apiRequest = (path, options = {}, retried = false) => {
  const method = (options.method || 'GET').toUpperCase();
  if (method !== 'GET' && method !== 'HEAD') {
    pendingReads.clear();
    return sendApiRequest(path, options, retried).finally(() => pendingReads.clear());
  }
  // Share only concurrent default GETs; downloads and custom requests remain independent.
  if (Object.keys(options).length || retried) return sendApiRequest(path, options, retried);
  const key = JSON.stringify([path, localStorage.getItem('access_token')]);
  if (!pendingReads.has(key)) {
    const request = sendApiRequest(path, options, retried).finally(() => {
      if (pendingReads.get(key) === request) pendingReads.delete(key);
    });
    pendingReads.set(key, request);
  }
  return pendingReads.get(key);
};

export const downloadApiFile = async (path, filename, expectedType = 'application/pdf') => {
  const blob = await apiRequest(path, { responseType: 'blob', headers: { Accept: '*/*' } });
  if (blob.type.split(';')[0] !== expectedType) throw new Error('Le serveur n’a pas renvoyé le format de fichier demandé.');
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.append(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
};

export const formatApiError = (data) => {
  if (typeof data === 'string') return data;
  if (!data || typeof data !== 'object') return 'Une erreur inconnue est survenue.';
  const messages = Object.entries(data).flatMap(([field, value]) => {
    const label = field === 'non_field_errors' || field === 'detail' ? '' : `${field} : `;
    return (Array.isArray(value) ? value : [value]).map((item) =>
      `${label}${typeof item === 'string' ? item : JSON.stringify(item)}`
    );
  });
  return messages.join(' ' ) || 'Une erreur inconnue est survenue.';
};

export const login = async (email, password) => {
  const response = await fetch(`${apiBase}/api/auth/login/`, {
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    let message = formatApiError(data);
    if (response.status === 401 || response.status === 400) message = 'Adresse email ou mot de passe incorrect.';
    else if (response.status === 404) message = 'Le service de connexion est introuvable. Vérifiez la configuration de l’API Django.';
    else if (response.status >= 500) message = 'Le serveur RH est indisponible. Vérifiez que Django est démarré.';
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }
  if (!data.access || !data.refresh || !data.user) throw new Error('La réponse du serveur est incomplète.');
  localStorage.setItem('access_token', data.access);
  localStorage.setItem('refresh_token', data.refresh);
  localStorage.setItem('user', JSON.stringify(data.user));
  return data.user;
};
