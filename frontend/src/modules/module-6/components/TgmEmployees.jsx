import React, { useState } from 'react';
import TgmTableControls from './TgmTableControls.jsx';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../../../shared/components/ui/table.jsx';
import { amount } from '../lib/tgm.js';
import TgmPanel from './TgmPanel.jsx';

export default function TgmEmployees({ report }) {
  const [query, setQuery] = useState('');
  const [sort, setSort] = useState('name');
  const [page, setPage] = useState(1);
  const rows = report.employes.filter((row) => `${row.employe_prenom} ${row.employe_nom} ${row.matricule} ${row.departement || ''}`.toLocaleLowerCase('fr').includes(query.toLocaleLowerCase('fr')))
    .sort((a, b) => sort === 'name' ? a.employe_nom.localeCompare(b.employe_nom, 'fr') : (Number(b[sort]) || 0) - (Number(a[sort]) || 0));
  const currentPage = Math.min(page, Math.max(1, Math.ceil(rows.length / 10)));
  const visible = rows.slice((currentPage - 1) * 10, currentPage * 10);
  return <TgmPanel title="Taux moyens par employé" description="Taux journalier = montant / jours prévus. Taux horaire = montant / heures prévues au contrat.">
    <TgmTableControls query={query} setQuery={setQuery} sort={sort} setSort={setSort} page={currentPage} setPage={setPage} count={rows.length}
      options={ [['name', 'Nom'], ['cout_charge_total', 'Coût chargé décroissant'], ['taux_journalier_charge', 'Taux journalier décroissant'], ['taux_horaire_charge', 'Taux horaire décroissant']] } />
    {report.employes.length > 0 && !rows.length ? <p role="status">Aucun employé ne correspond à la recherche.</p> : null}
    {!report.employes.length ? <p role="status">Aucune paie validée ou payée sur cette période.</p> : <Table containerProps={{ tabIndex: 0, role: 'region', 'aria-label': 'Taux par employé, tableau défilant' }}>
      <caption className="sr-only">Montants et taux journaliers et horaires par employé et devise</caption>
      <TableHeader><TableRow>
        {['Employé', 'Mois inclus', 'Jours prévus', 'Heures prévues', 'Brut total', 'Coût chargé total', 'Taux journalier brut', 'Taux journalier chargé', 'Taux horaire brut', 'Taux horaire chargé', 'Disponibilité'].map((label) => <TableHead key={label} scope="col">{label}</TableHead>)}
      </TableRow></TableHeader>
      <TableBody>{visible.map((row) => <TableRow key={`${row.employe_id}-${row.devise}`}>
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
