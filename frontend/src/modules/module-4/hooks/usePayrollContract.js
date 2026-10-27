import { useEffect, useState } from 'react';
import { apiRequest, formatApiError } from '../../../shared/lib/api.js';

export default function usePayrollContract(employeeId, period) {
  const key = `${employeeId}:${period}`;
  const ready = Boolean(employeeId) && /^\d{4}-(0[1-9]|1[0-2])$/.test(period);
  const [state, setState] = useState({ key: '', context: null, error: '', loading: false });
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    if (!ready) return;
    let active = true;
    setState({ key, context: null, error: '', loading: true });
    const query = new URLSearchParams({ employe: employeeId, periode: period });
    apiRequest(`/api/paiements/contexte-contrat/?${query}`).then(
      (context) => { if (active) setState({ key, context, loading: false, error: '' }); },
      (error) => { if (active) setState({ key, context: null, loading: false, error: formatApiError(error.details || error.message) }); },
    );
    return () => { active = false; };
  }, [employeeId, period, key, ready, attempt]);
  const current = state.key === key && ready ? state : { context: null, error: '', loading: ready };
  return { ...current, ready, retry: () => setAttempt((value) => value + 1) };
}
