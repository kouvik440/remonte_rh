import React, { useState } from 'react';
import FormField from '../../../shared/components/FormField.jsx';
import { validatePeriod } from '../lib/tgm.js';
import TgmPanel from './TgmPanel.jsx';

export default function TgmFilters({ applied, busy, onApply }) {
  const [draft, setDraft] = useState(applied);
  const [errors, setErrors] = useState({});
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
      <button type="submit" className="primary-button" disabled={busy}>Afficher les coûts</button>
    </form>
    <p className="tgm-note">Période appliquée : {applied.start} à {applied.end}.</p>
  </TgmPanel>;
}
