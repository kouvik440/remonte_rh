import React from 'react';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../../../shared/components/ui/table.jsx';
import { amount } from '../lib/tgm.js';
import TgmPanel from './TgmPanel.jsx';

export default function TgmEmployees({ report }) {
  return <TgmPanel title="Taux moyens par employé" description="Taux journalier = montant / jours prévus. Taux horaire = montant / heures prévues au contrat.">
    {!report.employes.length ? <p role="status">Aucune paie validée ou payée sur cette période.</p> : <Table containerProps={{ tabIndex: 0, role: 'region', 'aria-label': 'Taux par employé, tableau défilant' }}>
      <caption className="sr-only">Montants et taux journaliers et horaires par employé et devise</caption>
      <TableHeader><TableRow>
        {['Employé', 'Mois inclus', 'Jours prévus', 'Heures prévues', 'Brut total', 'Coût chargé total', 'Taux journalier brut', 'Taux journalier chargé', 'Taux horaire brut', 'Taux horaire chargé', 'Disponibilité'].map((label) => <TableHead key={label} scope="col">{label}</TableHead>)}
      </TableRow></TableHeader>
      <TableBody>{report.employes.map((row) => <TableRow key={`${row.employe_id}-${row.devise}`}>
        <TableHead scope="row">{row.employe_prenom} {row.employe_nom}<br /><small>{row.matricule} · {row.devise}</small></TableHead>
        <TableCell>{row.periodes.join(', ')}</TableCell>
        <TableCell>{row.jours_ouvres_previsionnels}</TableCell>
        <TableCell>{row.heures_previsionnelles ?? 'Indisponible'}</TableCell>
        {['salaire_brut_total', 'cout_charge_total', 'taux_journalier_brut', 'taux_journalier_charge', 'taux_horaire_brut', 'taux_horaire_charge'].map((key) => <TableCell key={key}>{amount(row[key], row.devise)}</TableCell>)}
        <TableCell className="tgm-reason">{[row.motif_indisponibilite, row.motif_indisponibilite_horaire].filter(Boolean).join(' ') || 'Taux disponibles'}</TableCell>
      </TableRow>)}</TableBody>
    </Table>}
    <p className="tgm-note">{report.note}</p>
  </TgmPanel>;
}
