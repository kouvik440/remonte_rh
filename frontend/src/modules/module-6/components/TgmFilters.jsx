import React, { useEffect, useState } from 'react';
import FormField from '../../../shared/components/FormField.jsx';
import { validatePeriod } from '../lib/tgm.js';
import TgmPanel from './TgmPanel.jsx';

export default function TgmFilters({ applied, busy, onApply, employees = [] }) {
  const [draft, setDraft] = useState(applied);
  const [errors, setErrors] = useState({});
  const [available, setAvailable] = useState(employees);
  useEffect(() => {
    if (employees.length && !applied.department && !applied.employee) setAvailable(employees);
  }, [employees, applied.department, applied.employee]);
  function submit(event) {
    event.preventDefault();
    const nextErrors = validatePeriod(draft);
    setErrors(nextErrors);
    if (!Object.keys(nextErrors).length) onApply({ ...draft });
  }
  return <TgmPanel title="Période d’analyse" description="Les taux couvrent les mois ayant une paie validée ou payée. Les coûts projets suivent les heures validées de cette période.">
    <form className="form-grid tgm-filters" onSubmit={submit} noValidate aria-busy={busy}>
      {[['start', 'Début'], ['end', 'Fin']].map(([field, label]) => <FormField key={field} label={label} error={errors[field]}>
        {(accessibility) => <input {...accessibility} aria-label={label} type="month" min="0001-01" max="9999-12" value={draft[field]} required disabled={busy}
          onChange={(event) => setDraft((current) => ({ ...current, [field]: event.target.value }))} />}
      </FormField>)}
      <FormField label="Département des taux">{(a11y) => <select {...a11y} value={draft.department || ''} disabled={busy} onChange={(event) => setDraft((current) => ({ ...current, department: event.target.value, employee: '' }))}>
        <option value="">Tous les départements</option>{Array.from(new Map(available.filter((row) => row.departement_id).map((row) => [row.departement_id, row])).values()).map((row) => <option key={row.departement_id} value={row.departement_id}>{row.departement}</option>)}
      </select>}</FormField>
      <FormField label="Employé des taux">{(a11y) => <select {...a11y} value={draft.employee || ''} disabled={busy} onChange={(event) => setDraft((current) => ({ ...current, employee: event.target.value }))}>
        <option value="">Tous les employés</option>{Array.from(new Map(available.filter((row) => !draft.department || String(row.departement_id) === String(draft.department)).map((row) => [row.employe_id, row])).values()).map((row) => <option key={row.employe_id} value={row.employe_id}>{row.employe_prenom} {row.employe_nom}</option>)}
      </select>}</FormField>
      <button type="submit" className="primary-button" disabled={busy}>Afficher les coûts</button>
    </form>
    <p className="tgm-note">Période appliquée : {applied.start} à {applied.end}. Les filtres département et employé concernent les taux ; les coûts projets conservent le périmètre de la période.</p>
  </TgmPanel>;
}
