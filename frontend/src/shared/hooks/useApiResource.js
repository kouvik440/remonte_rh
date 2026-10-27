import { navigate } from '../lib/navigation.js';
import { useCallback, useEffect, useState } from 'react';
import { apiRequest, clearSession, formatApiError } from '../lib/api.js';

export default function useApiResource(path, enabled = true, { refreshOnFocus = false } = {}) {
  const [state, setState] = useState({ path: null, revision: -1, report: null, error: '', loading: true });
  const [revision, setRevision] = useState(0);
  const reload = useCallback(() => setRevision((value) => value + 1), []);
  useEffect(() => {
    if (!enabled) return;
    let current = true;
    setState({ path, revision, report: null, error: '', loading: true });
    apiRequest(path).then((report) => {
      if (current) setState({ path, revision, report, error: '', loading: false });
    }).catch((failure) => {
      if (!current) return;
      if (failure.status === 401) {
        clearSession(); navigate('/connexion?session=expired', { replace: true }); return;
      }
      setState({ path, revision, report: null, error: formatApiError(failure.details || failure.message), loading: false });
    });
    return () => { current = false; };
  }, [path, enabled, revision]);
  useEffect(() => {
    if (!enabled || !refreshOnFocus) return;
    const onVisible = () => { if (document.visibilityState === 'visible') reload(); };
    window.addEventListener('focus', onVisible);
    document.addEventListener('visibilitychange', onVisible);
    return () => {
      window.removeEventListener('focus', onVisible);
      document.removeEventListener('visibilitychange', onVisible);
    };
  }, [enabled, refreshOnFocus, reload]);
  const ready = enabled && state.path === path && state.revision === revision;
  return { report: ready ? state.report : null, error: ready ? state.error : '',
    loading: enabled && (!ready || state.loading), reload };
}
