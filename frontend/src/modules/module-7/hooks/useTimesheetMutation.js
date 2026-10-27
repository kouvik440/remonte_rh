import { navigate } from '../../../shared/lib/navigation.js';
import { useRef, useState } from 'react';
import { apiRequest, clearSession } from '../../../shared/lib/api.js';
import { readableError } from '../lib/timesheets.js';

export default function useTimesheetMutation() {
  const lock = useRef(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function run(path, method, payload, onSuccess) {
    if (lock.current) return false;
    lock.current = true; setBusy(true); setError('');
    try {
      const result = await apiRequest(path, { method, ...(payload !== undefined ? { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) } : {}) });
      await onSuccess?.(result);
      return true;
    } catch (failure) {
      if (failure.status === 401) {
        clearSession(); navigate('/connexion?session=expired', { replace: true });
      } else setError(readableError(failure.details || failure.message));
      return false;
    } finally { lock.current = false; setBusy(false); }
  }
  return { busy, error, run, reset: () => setError('') };
}
