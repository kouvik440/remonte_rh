import React from 'react';
import { money } from '../lib/payrollMass.js';
import { massColumns } from '../lib/massMetrics.js';
import MassPanel from './MassPanel.jsx';
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '../../../shared/components/ui/table.jsx';

export default function MassBreakdown({ title, rows, labelKey, idKey, note }) {
  return <MassPanel title={title}>
    {note && <p className="mass-note">{note}</p>}
    {!rows.length ? <p className="leave-state">Aucune paie validée ou payée pour cette ventilation.</p> : <Table className="mass-data-table" containerProps={{ tabIndex: 0, role: 'region', 'aria-label': title }}>
      <TableCaption>{title} — montants en XOF</TableCaption>
      <TableHeader><TableRow><TableHead scope="col">{title}</TableHead>
        {massColumns.map((column) => <TableHead scope="col" key={column.key}>{column.label}</TableHead>)}
      </TableRow></TableHeader>
      <TableBody>{rows.map((row) => <TableRow key={row[idKey]}><TableHead scope="row">{row[labelKey]}</TableHead>
        {massColumns.map((column) => <TableCell key={column.key}>{column.amount ? money(row[column.key]) : row[column.key]}</TableCell>)}
      </TableRow>)}</TableBody>
    </Table>}
  </MassPanel>;
}
