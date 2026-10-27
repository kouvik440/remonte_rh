import React from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../../shared/components/ui/table.jsx';

export default function TimesheetLines({ sheet }) {
  return <>
    <p className="timesheet-note">{sheet.total_heures} h sur {sheet.jours_saisis} date(s) renseignée(s). Les journées saisies sont enregistrées en heures selon le contrat.</p>
    {!sheet.lignes.length ? <p>Aucune ligne enregistrée.</p> : <Table containerProps={{ tabIndex: 0, role: 'region', 'aria-label': `Détail de la semaine du ${sheet.semaine_debut}` }}>
      <caption className="sr-only">Temps déclaré par date, projet et tâche</caption>
      <TableHeader><TableRow>{['Date', 'Projet', 'Tâche', 'Heures', 'Commentaire'].map((label) => <TableHead scope="col" key={label}>{label}</TableHead>)}</TableRow></TableHeader>
      <TableBody>{sheet.lignes.map((line) => <TableRow key={line.id}>
        <TableHead scope="row">{line.date_travail}</TableHead><TableCell>{line.projet_nom}</TableCell>
        <TableCell>{line.tache_nom}</TableCell><TableCell>{line.heures} h</TableCell><TableCell className="timesheet-comment">{line.commentaire || '—'}</TableCell>
      </TableRow>)}</TableBody>
    </Table>}
    {sheet.motif_refus && <p className="message-box" role="status">Retour du manager : {sheet.motif_refus}</p>}
    {sheet.date_decision && <p className="timesheet-note">Décision du {sheet.date_decision.slice(0, 10)} · {sheet.valideur_prenom} {sheet.valideur_nom}</p>}
  </>;
}
