import { useRef, useState } from 'react';
import useApiMutation from '../../../shared/hooks/useApiMutation.js';
import { downloadApiFile, formatApiError } from '../../../shared/lib/api.js';
import { actionLabels, payrollPath } from '../lib/payroll.js';

export default function usePayrollActions(onChanged) {
  const mutation = useApiMutation(onChanged);
  const [editor, setEditor] = useState(null);
  const [notice, setNotice] = useState('');
  const [downloadError, setDownloadError] = useState('');
  const [downloading, setDownloading] = useState(false);
  const downloadLock = useRef(false);
  const download = async (payroll) => {
    if (downloadLock.current) return;
    downloadLock.current = true; setDownloading(true);
    try { await downloadApiFile(`${payrollPath}${payroll.id}/bulletin/`, `bulletin-paie-${payroll.periode}-${payroll.id}.pdf`); }
    catch (error) { setDownloadError(formatApiError(error.details || error.message)); }
    finally { downloadLock.current = false; setDownloading(false); }
  };
  const openAction = (action, payroll = null) => {
    mutation.reset(); setNotice(''); setDownloadError('');
    if (action === 'download') { download(payroll); return; }
    setEditor({ action, payroll });
  };
  const saved = () => {
    setNotice(editor.action === 'validate' ? 'Paie validée. Le bulletin PDF est archivé et disponible au téléchargement.'
      : ['create', 'edit'].includes(editor.action) ? 'Brouillon enregistré.' : `${actionLabels[editor.action]} : opération effectuée.`);
    setEditor(null);
  };
  return { mutation, editor, notice, downloadError, downloading, busy: mutation.saving || downloading,
    openAction, saved, closeEditor: () => setEditor(null) };
}
