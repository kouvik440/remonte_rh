import { useRef, useState } from 'react';
import { downloadApiFile, formatApiError } from '../../../shared/lib/api.js';
import { transfersPath } from '../lib/transfers.js';

export default function useTransferDocumentDownload() {
  const lock = useRef(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const download = async (order) => {
    if (lock.current) return;
    lock.current = true; setBusy(true); setError('');
    try { await downloadApiFile(`${transfersPath}${order.id}/document/`, `ordre-virement-BF-${order.id}.pdf`); }
    catch (failure) { setError(formatApiError(failure.details || failure.message)); }
    finally { lock.current = false; setBusy(false); }
  };
  return { busy, error, download };
}
