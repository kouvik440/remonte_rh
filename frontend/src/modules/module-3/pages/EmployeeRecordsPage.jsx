import React, { useCallback, useEffect, useRef, useState } from 'react';
import { navigate } from '../../../shared/lib/navigation.js';
import { apiRequest, clearSession, formatApiError, getUser, hasPermission } from '../../../shared/lib/api.js';
import RecordManager from '../components/RecordManager.jsx';
import { canAct, resources } from '../lib/resources.js';

const emptyData = () => ({ bank: [], employees: [] });

export default function EmployeeRecordsPage() {
  const [user] = useState(getUser);
  const [data, setData] = useState(emptyData);
  const [loading, setLoading] = useState(true);
  const [errors, setErrors] = useState({});
  const version = useRef(0);
  const bankRead = canAct('bank', 'read');
  const employeeRead = bankRead && hasPermission('employe.read') && hasPermission('coordonnees_bancaires.manage');
  const load = useCallback(async () => {
    const current = ++version.current;
    setLoading(true);
    const tasks = [
      ...(bankRead ? [['bank', resources.bank.path]] : []),
      ...(employeeRead ? [['employees', '/api/employes/']] : []),
    ];
    const results = await Promise.allSettled(tasks.map(([, path]) => apiRequest(path)));
    if (current !== version.current) return;
    const nextData = emptyData();
    const nextErrors = {};
    results.forEach((result, index) => {
      const [key] = tasks[index];
      if (result.status === 'fulfilled') nextData[key] = result.value;
      else nextErrors[key] = formatApiError(result.reason.details || result.reason.message);
    });
    if (results.some((result) => result.status === 'rejected' && result.reason.status === 401)) {
      clearSession(); navigate('/connexion?session=expired', { replace: true }); return;
    }
    setData(nextData); setErrors(nextErrors); setLoading(false);
  }, [bankRead, employeeRead]);
  useEffect(() => {
    if (!localStorage.getItem('access_token')) { navigate('/connexion', { replace: true }); return; }
    if (!Array.isArray(user?.permissions)) {
      clearSession(); navigate('/connexion?session=permissions', { replace: true }); return;
    }
    load();
    return () => { version.current += 1; };
  }, [load, user]);
  if (!localStorage.getItem('access_token') || !Array.isArray(user?.permissions)) return null;
  return <>
    <section className="page-heading"><div>
      <h1>Coordonnées bancaires</h1><p className="page-description">Consultez et gérez les coordonnées bancaires selon vos droits.</p>
    </div></section>
    {errors.employees && <p className="message-box error" role="alert">Liste des employés : {errors.employees}</p>}
    {!bankRead && <p className="message-box error" role="alert">Votre compte ne possède aucune permission de consultation bancaire.</p>}
    {bankRead && <RecordManager kind="bank" records={data.bank}
      employees={data.employees} loading={loading} error={errors.bank || ''} onChanged={load} />}
  </>;
}
