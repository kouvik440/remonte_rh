import React, { useState } from 'react';
import FormField from '../../../shared/components/FormField.jsx';
import useTgmReport from '../hooks/useTgmReport.js';
import { amount, reportPaths } from '../lib/tgm.js';
import TgmPanel from './TgmPanel.jsx';

export default function TgmSimulation({ projects, period }) {
  const [project, setProject] = useState('');
  const [revenue, setRevenue] = useState('');
  const [errors, setErrors] = useState({});
  const [query, setQuery] = useState(null);
  const data = useTgmReport(query, Boolean(query));
  function submit(event) {
    event.preventDefault();
    const nextErrors = {};
    if (!projects.some((row) => String(row.projet_id) === project)) nextErrors.project = 'Choisissez un projet.';
    const normalized = revenue.trim().replace(',', '.');
    if (!/^\d{1,12}(\.\d{1,2})?$/.test(normalized)) nextErrors.revenue = 'Saisissez un montant positif ou nul avec deux décimales au maximum.';
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;
    const params = new URLSearchParams(reportPaths(period).costs.split('?')[1]);
    params.set('projet', project); params.set('chiffre_affaires', normalized);
    const path = `/api/analyses/couts-projets/simulation/?${params}`;
    if (query === path) data.reload(); else setQuery(path);
  }
  const report = data.report;
  return <TgmPanel title="Simuler la rentabilité" description="Comparez le chiffre d’affaires de la période au coût du personnel. Le scénario reste temporaire.">
    {!projects.length ? <p role="status">La simulation nécessite un projet avec des heures validées sur la période.</p> : <>
      <form className="form-grid tgm-filters" onSubmit={submit} noValidate aria-busy={data.loading}>
        <FormField label="Projet / prestation" error={errors.project}>{(accessibility) => <select {...accessibility} aria-label="Projet / prestation" required value={project} disabled={data.loading}
          onChange={(event) => { setProject(event.target.value); setQuery(null); }}>
          <option value="">Choisir un projet</option>
          {projects.map((row) => <option key={row.projet_id} value={row.projet_id}>{row.projet_code} · {row.projet_nom}</option>)}
        </select>}</FormField>
        <FormField label="Chiffre d’affaires de la période (XOF)" error={errors.revenue}>{(accessibility) => <input {...accessibility} aria-label="Chiffre d’affaires de la période (XOF)" inputMode="decimal" required value={revenue} disabled={data.loading}
          placeholder="Ex. 1500000" onChange={(event) => { setRevenue(event.target.value); setQuery(null); }} />}</FormField>
        <button className="primary-button" type="submit" disabled={data.loading}>Calculer la marge</button>
      </form>
      {data.loading && <p role="status">Calcul de la simulation…</p>}
      {data.error && <p className="message-box error" role="alert">{data.error}</p>}
      {report && <div aria-live="polite">
        <p className="tgm-note">Scénario : {report.projet_nom}, du {report.date_debut} au {report.date_fin}.</p>
        <dl className="tgm-simulation-results">
          <div><dt>Chiffre d’affaires saisi</dt><dd>{amount(report.chiffre_affaires)}</dd></div>
          <div><dt>Coût estimé du personnel</dt><dd>{amount(report.cout_estime)}</dd></div>
          <div><dt>Marge après coût du personnel</dt><dd>{amount(report.marge_personnel)}</dd></div>
          <div><dt>Marge / chiffre d’affaires</dt><dd>{report.taux_marge_personnel === null ? 'Indisponible' : `${report.taux_marge_personnel} %`}</dd></div>
        </dl>
        {!report.cout_complet && <p className="message-box" role="status">Marge indisponible : {report.heures_sans_tgm} heures sans taux. Le coût calculable de {amount(report.cout_calculable)} est partiel.</p>}
        <p className="tgm-note">{report.note}</p>
      </div>}
    </>}
  </TgmPanel>;
}
