import { navigate } from '../../../shared/lib/navigation.js';
import { useCallback, useEffect, useRef, useState } from 'react';
import { apiRequest, clearSession, formatApiError } from '../../../shared/lib/api.js';
import { payrollPath } from '../lib/payroll.js';

const emptyData = () => ({ payrolls: [], employees: [], rules: [], orders: [] });

export default function usePayrollData({ read, employees, rules, orders }) {
  const [data, setData] = useState(emptyData);
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(true);
  const version = useRef(0);
  const load = useCallback(async () => {
    const requestVersion = ++version.current;
    setLoading(true);
    setErrors({});
    const tasks = [
      ...(read ? [['payrolls', payrollPath]] : []),
      ...(read && employees ? [['employees', '/api/employes/']] : []),
      ...(read && rules ? [['rules', '/api/regles-paie/']] : []),
      ...(orders ? [['orders', '/api/ordres-virement/']] : []),
    ];
    const results = await Promise.allSettled(tasks.map(([, path]) => apiRequest(path)));
    if (requestVersion !== version.current) return;
    const nextData = emptyData();
    const nextErrors = {};
    results.forEach((result, index) => {
      const key = tasks[index][0];
      if (result.status === 'fulfilled') nextData[key] = result.value;
      else nextErrors[key] = formatApiError(result.reason.details || result.reason.message);
    });
    if (results.some((result) => result.status === 'rejected' && result.reason.status === 401)) {
      clearSession(); navigate('/connexion?session=expired', { replace: true }); return;
    }
    setData(nextData); setErrors(nextErrors); setLoading(false);
  }, [read, employees, rules, orders]);
  useEffect(() => {
    load();
    return () => { version.current += 1; };
  }, [load]);
  return { ...data, errors, loading, load };
}
