import React from 'react';
import { money, periodLabel } from '../lib/payrollMass.js';
import { evolutionMetrics, massColumns } from '../lib/massMetrics.js';
import MassPanel from './MassPanel.jsx';
import MassComparisonChart from './MassComparisonChart.jsx';
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '../../../shared/components/ui/table.jsx';

export default function MassEvolution({ data }) {
  const rows = data.evolution;
  return <MassPanel title={`Évolution ${data.granularite === 'annuelle' ? 'annuelle' : data.granularite === 'trimestrielle' ? 'trimestrielle' : 'mensuelle'}`} description="Salaires nets, coût employeur et cotisations en XOF · périodes comportant des paies">
    {!rows.length ? <p className="leave-state">Aucune évolution disponible sur cette période.</p> : <>
      <p className="mass-note">Bleu : paies validées en attente de paiement. Vert : paies payées. Chaque graphique possède sa propre échelle.</p>
      <div className="mass-comparisons">{evolutionMetrics.map((metric) => <MassComparisonChart key={metric.validatedKey} rows={rows} metric={metric} />)}</div>
      <Table className="mass-data-table" containerProps={{ role: 'region', 'aria-label': 'Données de l’évolution', tabIndex: 0 }}>
        <TableCaption>Évolution du brut, du net, des cotisations et du coût employeur en XOF</TableCaption>
        <TableHeader><TableRow><TableHead scope="col">Période</TableHead><TableHead scope="col">Employés distincts</TableHead>
          {massColumns.map((column) => <TableHead scope="col" key={column.key}>{column.label}</TableHead>)}
        </TableRow></TableHeader>
        <TableBody>{rows.map((row) => <TableRow key={row.periode || row.annee || row.trimestre}>
          <TableHead scope="row">{periodLabel(row.periode || row.annee || row.trimestre)}</TableHead><TableCell>{row.employes}</TableCell>
          {massColumns.map((column) => <TableCell key={column.key}>{column.amount ? money(row[column.key]) : row[column.key]}</TableCell>)}
        </TableRow>)}</TableBody>
      </Table>
    </>}
  </MassPanel>;
}
