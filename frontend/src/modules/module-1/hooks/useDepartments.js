import { navigate } from '../../../shared/lib/navigation.js';
import { useCallback, useEffect, useRef, useState } from 'react';
import { apiRequest, clearSession, formatApiError } from '../../../shared/lib/api.js';

export default function useDepartments(enabled) {
  const [state, setState] = useState({ departments: [], loading: true, error: '' });
  const version = useRef(0);
  const load = useCallback(async () => {
    if (!enabled) return;
    const current = ++version.current;
    setState((value) => ({ ...value, loading: true, error: '' }));
    try {
      const departments = await apiRequest('/api/departements/');
      if (current === version.current) setState({ departments, loading: false, error: '' });
    } catch (error) {
      if (current !== version.current) return;
      if (error.status === 401) {
        clearSession(); navigate('/connexion?session=expired', { replace: true }); return;
      }
      setState({ departments: [], loading: false, error: formatApiError(error.details || error.message) });
    }
  }, [enabled]);
  useEffect(() => {
    load();
    return () => { version.current += 1; };
  }, [load]);
  return { ...state, loading: enabled && state.loading, load };
}
