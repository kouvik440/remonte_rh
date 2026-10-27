import { useRef, useState } from 'react';
import { apiRequest, formatApiError } from '../lib/api.js';

export default function useApiMutation(onChanged) {
  const lock = useRef(false);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState('');
  const submit = async (path, method, payload) => {
    if (lock.current) return false;
    lock.current = true;
    setSaving(true);
    setErrors({});
    setMessage('');
    try {
      await apiRequest(path, {
        method,
        ...(payload ? { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) } : {}),
      });
      await onChanged();
      return true;
    } catch (error) {
      setErrors(error.details && typeof error.details === 'object' ? error.details : {});
      setMessage(formatApiError(error.details || error.message));
      return false;
    } finally {
      lock.current = false;
      setSaving(false);
    }
  };
  return { saving, errors, message, submit, reset: () => { setErrors({}); setMessage(''); } };
}
