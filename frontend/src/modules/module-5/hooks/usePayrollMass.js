import { navigate } from '../../../shared/lib/navigation.js';
import { useEffect, useState } from 'react';
import { apiRequest, clearSession, formatApiError } from '../../../shared/lib/api.js';
import { analysisPath, analysisQuery } from '../lib/payrollMass.js';

export default function usePayrollMass(filters, enabled, canReadDepartments) {
  const [report, setReport] = useState(null);
  const [departments, setDepartments] = useState([]);
  const [departmentError, setDepartmentError] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [revision, setRevision] = useState(0);
  const [loadedFilters, setLoadedFilters] = useState(null);
  useEffect(() => {
    if (!enabled) { setLoading(false); return; }
    let current = true;
    setLoading(true); setError(''); setReport(null);
    apiRequest(`${analysisPath}?${analysisQuery(filters)}`).then((result) => {
      if (!current) return;
      setReport(result);
    }).catch((failure) => {
      if (!current) return;
      if (failure.status === 401) {
        clearSession(); navigate('/connexion?session=expired', { replace: true }); return;
      }
      setError(formatApiError(failure.details || failure.message));
    }).finally(() => {
      if (!current) return;
      setLoadedFilters(filters);
      setLoading(false);
    });
    return () => { current = false; };
  }, [filters, enabled, revision]);
  useEffect(() => {
    if (!enabled || !canReadDepartments) return;
    let current = true;
    apiRequest('/api/departements/').then((items) => {
      if (current) { setDepartments(items); setDepartmentError(''); }
    }).catch((failure) => { if (current) setDepartmentError(formatApiError(failure.details || failure.message)); });
    return () => { current = false; };
  }, [enabled, canReadDepartments, revision]);
  const ready = loadedFilters === filters;
  const evolution = report ? { granularite: filters.granularity, evolution: report[`evolution_${filters.granularity}`] } : null;
  return { report: ready ? report : null, evolution: ready ? evolution : null,
    departments, departmentError, loading: enabled && (!ready || loading), error,
    reload: () => setRevision((value) => value + 1) };
}
