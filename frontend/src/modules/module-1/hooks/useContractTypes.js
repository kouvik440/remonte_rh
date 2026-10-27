import { navigate } from '../../../shared/lib/navigation.js';
import { useCallback, useEffect, useRef, useState } from 'react';
import { apiRequest, clearSession, formatApiError } from '../../../shared/lib/api.js';

export default function useContractTypes() {
  const [state, setState] = useState({ types: [], loading: true, error: '' });
  const version = useRef(0);
  const load = useCallback(async () => {
    const current = ++version.current;
    setState((value) => ({ ...value, loading: true, error: '' }));
    try {
      const types = await apiRequest('/api/types-contrat/');
      if (current === version.current) setState({ types, loading: false, error: '' });
    } catch (error) {
      if (current !== version.current) return;
      if (error.status === 401) { clearSession(); navigate('/connexion?session=expired', { replace: true }); return; }
      setState({ types: [], loading: false, error: formatApiError(error.details || error.message) });
    }
  }, []);
  useEffect(() => { load(); return () => { version.current += 1; }; }, [load]);
  return { ...state, load };
}
