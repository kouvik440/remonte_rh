import React, { useState } from 'react';
import { money } from '../lib/payrollMass.js';
import { massColumns } from '../lib/massMetrics.js';
import MassPanel from './MassPanel.jsx';
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '../../../shared/components/ui/table.jsx';

export default function MassBreakdown({ title, rows, labelKey, idKey, note }) {
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState('label');
  const [page, setPage] = useState(0);
  const filtered = rows.filter(row => String(row[labelKey]).toLocaleLowerCase('fr').includes(search.toLocaleLowerCase('fr'))).sort((a,b) => sort === 'label' ? String(a[labelKey]).localeCompare(String(b[labelKey]), 'fr') : (Number(b.cout_employeur_valide)+Number(b.cout_employeur_paye))-(Number(a.cout_employeur_valide)+Number(a.cout_employeur_paye)));
  const pages = Math.max(1, Math.ceil(filtered.length / 10));
  const activePage = Math.min(page, pages - 1);
  const visible = filtered.slice(activePage * 10, activePage * 10 + 10);
  return <MassPanel title={title}>
    {note && <p className="mass-note">{note}</p>}
    <div className="mass-table-tools"><label>Rechercher <input type="search" value={search} onChange={event=>{setSearch(event.target.value);setPage(0);}} /></label>
      <label>Trier <select value={sort} onChange={event=>{setSort(event.target.value);setPage(0);}}><option value="label">Libellé A–Z</option><option value="cost">Coût employeur décroissant</option></select></label></div>
    {!filtered.length ? <p className="leave-state">Aucune paie validée ou payée pour cette ventilation.</p> : <Table className="mass-data-table" containerProps={{ tabIndex: 0, role: 'region', 'aria-label': title }}>
      <TableCaption>{title} — montants en XOF</TableCaption>
      <TableHeader><TableRow><TableHead scope="col">{title}</TableHead>
        {massColumns.map((column) => <TableHead scope="col" key={column.key}>{column.label}</TableHead>)}
      </TableRow></TableHeader>
      <TableBody>{visible.map((row) => <TableRow key={row[idKey]}><TableHead scope="row">{row[labelKey]}</TableHead>
        {massColumns.map((column) => <TableCell key={column.key}>{column.amount ? money(row[column.key]) : row[column.key]}</TableCell>)}
      </TableRow>)}</TableBody>
    </Table>}
    <div className="mass-table-tools" aria-label="Pagination"><button className="outline-button" type="button" disabled={activePage === 0} onClick={()=>setPage(activePage-1)}>Précédent</button><span role="status">Page {activePage+1} / {pages} · {filtered.length} résultat(s)</span><button className="outline-button" type="button" disabled={activePage+1 >= pages} onClick={()=>setPage(activePage+1)}>Suivant</button></div>
  </MassPanel>;
}
