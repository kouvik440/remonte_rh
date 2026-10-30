import React, { useState } from 'react';
import TgmPanel from './TgmPanel.jsx';
import FormField from '../../../shared/components/FormField.jsx';
import useTgmReport from '../hooks/useTgmReport.js';
import { amount, reportPaths } from '../lib/tgm.js';

export default function TgmProductiveSimulation({ period, employees }) {
  const [employee, setEmployee] = useState('');
  const [days, setDays] = useState('');
  const [hours, setHours] = useState('');
  const [error, setError] = useState('');
  const [path, setPath] = useState(null);
  const data = useTgmReport(path, Boolean(path));
  function submit(event) {
    event.preventDefault();
    if (!employee || (!days && !hours) || [days, hours].some((value) => value && (!/^\d+(\.\d{1,2})?$/.test(value) || Number(value) > 100000))) {
      setError('Choisissez un employé et saisissez des jours ou heures entre 0 et 100 000, avec deux décimales au maximum.'); return;
    }
    setError('');
    const params = new URLSearchParams(reportPaths(period).rates.split('?')[1]);
    params.set('employe', employee);
    if (days) params.set('jours_productifs', days);
    if (hours) params.set('heures_productives', hours);
    const next = `/api/analyses/tgm/?${params}`;
    if (next === path) data.reload(); else setPath(next);
  }
  if (!employees.length) return <TgmPanel title="Simuler les jours et heures productifs"><p role="status">Aucun employé avec une paie finalisée sur ce périmètre. Modifiez la période ou les filtres pour simuler un coût.</p></TgmPanel>;
  return <TgmPanel title="Simuler les jours et heures productifs" description="Projection temporaire calculée côté serveur avec les taux contractuels de la période. Les scénarios jours et heures sont indépendants.">
    <form className="form-grid tgm-filters" onSubmit={submit} aria-busy={data.loading}>
      <FormField label="Employé">{(a11y) => <select {...a11y} value={employee} onChange={(event) => { setEmployee(event.target.value); setPath(null); }} required>
        <option value="">Choisir un employé</option>{Array.from(new Map(employees.map((row) => [row.employe_id, row])).values()).map((row) => <option key={row.employe_id} value={row.employe_id}>{row.employe_prenom} {row.employe_nom} · {row.matricule}</option>)}
      </select>}</FormField>
      <FormField label="Jours productifs">{(a11y) => <input {...a11y} type="number" min="0" max="100000" step="0.01" value={days} onChange={(event) => { setDays(event.target.value); setPath(null); }} />}</FormField>
      <FormField label="Heures productives">{(a11y) => <input {...a11y} type="number" min="0" max="100000" step="0.01" value={hours} onChange={(event) => { setHours(event.target.value); setPath(null); }} />}</FormField>
      <button className="primary-button" type="submit" disabled={data.loading}>Simuler le coût</button>
    </form>
    {error || data.error ? <p className="message-box error" role="alert">{error || data.error}</p> : null}
    {data.loading ? <p role="status">Calcul du coût prévisionnel…</p> : null}
    {data.report ? <div aria-live="polite">{data.report.employes.map((row) => <dl className="tgm-simulation-results" key={`${row.employe_id}-${row.devise}`}>
      <div><dt>Scénario jours · {row.devise}</dt><dd>{amount(row.simulation?.cout_jours, row.devise)}</dd></div>
      <div><dt>Scénario heures · {row.devise}</dt><dd>{amount(row.simulation?.cout_heures, row.devise)}</dd></div>
    </dl>)}</div> : null}
  </TgmPanel>;
}
