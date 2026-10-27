import { useEffect, useState } from 'react';
import { apiRequest, formatApiError } from '../../../shared/lib/api.js';
import { transfersPath } from '../lib/transfers.js';

export default function useTransferDocumentContext(orderId) {
  const [state, setState] = useState({ loading: true, context: null, error: '' });
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    setState({ loading: true, context: null, error: '' });
    apiRequest(`${transfersPath}${orderId}/document/contexte/`).then(
      (context) => { if (active) setState({ loading: false, context, error: '' }); },
      (error) => { if (active) setState({ loading: false, context: null, error: formatApiError(error.details || error.message) }); },
    );
    return () => { active = false; };
  }, [orderId, attempt]);
  return { ...state, retry: () => setAttempt((value) => value + 1) };
}
