import { useState } from 'react';
import { downloadApiFile, formatApiError } from '../../../shared/lib/api.js';
import { massExportPath, exportTypes } from '../lib/payrollMass.js';

export default function useMassExport(filters) {
  const [downloading, setDownloading] = useState('');
  const [error, setError] = useState('');
  async function download(format) {
    if (downloading || !exportTypes[format]) return;
    setDownloading(format); setError('');
    try {
      await downloadApiFile(massExportPath(filters, format),
        `masse-salariale-${filters.start}-${filters.end}-${filters.granularity}${filters.department ? `-departement-${filters.department}` : ''}.${format}`, exportTypes[format]);
    } catch (failure) { setError(formatApiError(failure.details || failure.message)); }
    finally { setDownloading(''); }
  }
  return { downloading, error, download };
}
