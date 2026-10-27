import React, { useState } from 'react';
import AppLink from '../../../shared/components/AppLink.jsx';
import useApiResource from '../../../shared/hooks/useApiResource.js';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../../shared/components/ui/table.jsx';
import { currency, dateValue, parseDate } from '../lib/timesheets.js';
import TimesheetPanel from './TimesheetPanel.jsx';
import Field from './TimesheetField.jsx';
import ResourceState from './ResourceState.jsx';

function initialRange() {
  const start = new Date(); start.setDate(1);
  const end = new Date(); end.setMonth(end.getMonth() + 1, 0);
  return { start: dateValue(start), end: dateValue(end) };
}

export function CostReconciliation({ report }) {
  return <>
    <p className="timesheet-note">{report.date_debut} au {report.date_fin} · {report.totaux.heures_validees} h validées · Coût calculable : <strong>{currency(report.totaux.cout_calculable)}</strong>.</p>
    {!report.totaux.cout_complet && <p className="message-box" role="status">Coût incomplet : {report.totaux.heures_sans_tgm} h sans taux disponible. Une paie finalisée en XOF et un horaire contractuel complet sont nécessaires.</p>}
    {!report.rapprochement.length ? <p role="status">Aucune heure validée sur cette période. Les brouillons et feuilles soumises sont exclus.</p> : <Table containerProps={{ tabIndex: 0, role: 'region', 'aria-label': 'Rapprochement des heures validées et du TGM' }}>
      <caption className="sr-only">Coût par projet, employé et mois : heures validées multipliées par le taux horaire chargé</caption>
      <TableHeader><TableRow>{['Projet', 'Employé', 'Mois du taux', 'Heures validées', 'TGM horaire chargé', 'Coût estimé', 'Heures sans taux'].map((label) => <TableHead scope="col" key={label}>{label}</TableHead>)}</TableRow></TableHeader>
      <TableBody>{report.rapprochement.map((row) => <TableRow key={`${row.projet_id}-${row.employe_id}-${row.periode}`}>
        <TableHead scope="row">{row.projet_nom}</TableHead><TableCell>{row.employe_prenom} {row.employe_nom}<br /><small>{row.matricule}</small></TableCell>
        <TableCell>{row.periode}</TableCell><TableCell>{row.heures_validees} h</TableCell><TableCell>{currency(row.taux_horaire_charge)} / h</TableCell>
        <TableCell>{currency(row.cout_estime)}</TableCell><TableCell>{row.heures_sans_tgm} h</TableCell>
      </TableRow>)}</TableBody>
    </Table>}
    <p className="timesheet-note">Le coût utilise les heures réellement déclarées puis validées, au taux chargé mensuel du module 6. Le taux affiché est arrondi ; le calcul serveur conserve sa précision avant le montant final.</p>
    <AppLink className="outline-button" href="/tgm">Consulter les taux et simuler une marge</AppLink>
  </>;
}

export default function TimesheetCosts() {
  const [draft, setDraft] = useState(initialRange);
  const [range, setRange] = useState(initialRange);
  const [errors, setErrors] = useState({});
  const data = useApiResource(`/api/analyses/couts-projets/?${new URLSearchParams({ date_debut: range.start, date_fin: range.end })}`);
  function apply(event) {
    event.preventDefault();
    const next = {};
    for (const field of ['start', 'end']) if (!parseDate(draft[field])) next[field] = 'Choisissez une date valide.';
    if (!next.start && !next.end && draft.start > draft.end) next.end = 'La fin doit être égale ou postérieure au début.';
    setErrors(next);
    if (Object.keys(next).length) return;
    if (draft.start === range.start && draft.end === range.end) data.reload(); else setRange({ ...draft });
  }
  return <TimesheetPanel title="Rapprochement des temps et des coûts" description="Chaque validation alimente le module 6 : heures validées × taux horaire chargé du mois.">
    <form className="timesheet-filter" onSubmit={apply} noValidate>
      <Field label="Début du rapprochement" error={errors.start}><input type="date" value={draft.start} disabled={data.loading} onChange={(event) => setDraft((value) => ({ ...value, start: event.target.value }))} /></Field>
      <Field label="Fin du rapprochement" error={errors.end}><input type="date" value={draft.end} disabled={data.loading} onChange={(event) => setDraft((value) => ({ ...value, end: event.target.value }))} /></Field>
      <button className="primary-button" type="submit" disabled={data.loading}>Afficher le rapprochement</button>
    </form>
    <ResourceState data={data} label="du rapprochement">{(report) => <CostReconciliation report={report} />}</ResourceState>
  </TimesheetPanel>;
}
