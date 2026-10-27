import { navigate } from '../../../shared/lib/navigation.js';
import { useCallback, useEffect, useRef, useState } from 'react';
import { apiRequest, clearSession, formatApiError } from '../../../shared/lib/api.js';

export default function useEmployeeContracts(employeeId, readTypes, readPositions) {
  const [state, setState] = useState({ contracts: [], types: [], positions: [], loading: true, error: '', typesError: '', positionsError: '' });
  const version = useRef(0);
  const load = useCallback(async () => {
    const requestVersion = ++version.current;
    setState((value) => ({ ...value, loading: true, error: '', typesError: '' }));
    const results = await Promise.allSettled([
      apiRequest(`/api/contrats/?employe=${employeeId}`),
      readTypes ? apiRequest('/api/types-contrat/') : Promise.resolve([]),
      readPositions ? apiRequest('/api/postes/') : Promise.resolve([]),
    ]);
    if (requestVersion !== version.current) return;
    if (results.some((result) => result.status === 'rejected' && result.reason.status === 401)) {
      clearSession(); navigate('/connexion?session=expired', { replace: true }); return;
    }
    const failed = (result) => result?.status === 'rejected' ? formatApiError(result.reason.details || result.reason.message) : '';
    setState({ contracts: results[0].status === 'fulfilled' ? results[0].value : [],
      types: results[1]?.status === 'fulfilled' ? results[1].value : [],
      positions: results[2]?.status === 'fulfilled' ? results[2].value : [],
      loading: false, error: failed(results[0]), typesError: failed(results[1]), positionsError: failed(results[2]) });
  }, [employeeId, readTypes, readPositions]);
  useEffect(() => { load(); return () => { version.current += 1; }; }, [load]);
  return { ...state, load };
}
