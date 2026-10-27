import React, { useState } from 'react';
import FormField from '../../../shared/components/FormField.jsx';
import MassPanel from './MassPanel.jsx';
import MassSelect from './MassSelect.jsx';
import { validateFilters } from '../lib/payrollMass.js';

export default function MassFilters({ applied, departments, canReadDepartments, departmentError, busy, onApply }) {
  const [draft, setDraft] = useState(applied);
  const [errors, setErrors] = useState({});
  const change = (key) => (event) => setDraft((value) => ({ ...value, [key]: event.target.value }));
  function submit(event) {
    event.preventDefault();
    const nextErrors = validateFilters(draft);
    setErrors(nextErrors);
    if (!Object.keys(nextErrors).length) onApply({ ...draft });
  }
  const departmentOptions = [{ value: 'all', label: 'Tous les départements' },
    ...departments.map((item) => ({ value: String(item.id), label: item.nom }))];
  return <MassPanel title="Périmètre de l’analyse" description="Choisissez une période, puis appliquez vos filtres.">
    <form className="mass-filters form-grid" onSubmit={submit} aria-busy={busy}>
      <FormField label="Du mois de" error={errors.start}>{(a11y) => <input {...a11y} type="month" min="0001-01" max="9999-12" required value={draft.start} onChange={change('start')} />}</FormField>
      <FormField label="Au mois de" error={errors.end}>{(a11y) => <input {...a11y} type="month" min="0001-01" max="9999-12" required value={draft.end} onChange={change('end')} />}</FormField>
      <MassSelect label="Département" value={draft.department || 'all'} options={departmentOptions} disabled={!canReadDepartments || busy}
        onChange={(department) => setDraft((value) => ({ ...value, department: department === 'all' ? '' : department }))} />
      <MassSelect label="Évolution" value={draft.granularity} disabled={busy}
        options={[{ value: 'mensuelle', label: 'Par mois' }, { value: 'annuelle', label: 'Par année' }]}
        onChange={(granularity) => setDraft((value) => ({ ...value, granularity }))} />
      <button className="primary-button" type="submit" disabled={busy}>Afficher l’analyse</button>
    </form>
    {departmentError && <p className="message-box error" role="alert">Départements indisponibles : {departmentError}</p>}
    {!canReadDepartments && <p className="mass-note">Le filtre par département nécessite la permission departement.read. L’analyse globale reste disponible.</p>}
  </MassPanel>;
}
