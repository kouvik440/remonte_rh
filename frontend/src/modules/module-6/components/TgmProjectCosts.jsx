import React, { useState } from 'react';
import TgmTableControls from './TgmTableControls.jsx';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../../../shared/components/ui/table.jsx';
import { amount } from '../lib/tgm.js';
import TgmPanel from './TgmPanel.jsx';

function CostTable({ title, rows, label }) {
  return <Table containerProps={{ tabIndex: 0, role: 'region', 'aria-label': title }}>
    <caption>{title}</caption>
    <TableHeader><TableRow>{[label, 'Heures validées', 'Heures sans taux', 'Coût calculable (XOF)', 'Coût estimé complet (XOF)'].map((text) => <TableHead key={text} scope="col">{text}</TableHead>)}</TableRow></TableHeader>
    <TableBody>{rows.map((row) => <TableRow key={row.id}>
      <TableHead scope="row">{row.label}</TableHead><TableCell>{row.heures_validees}</TableCell><TableCell>{row.heures_sans_tgm}</TableCell>
      <TableCell>{amount(row.cout_calculable)}</TableCell><TableCell>{row.cout_complet ? amount(row.cout_estime) : 'Estimation incomplète'}</TableCell>
    </TableRow>)}</TableBody>
  </Table>;
}

export default function TgmProjectCosts({ report }) {
  const [query, setQuery] = useState('');
  const [sort, setSort] = useState('name');
  const [page, setPage] = useState(1);
  const projects = report.projets.filter((row) => `${row.projet_code} ${row.projet_nom}`.toLocaleLowerCase('fr').includes(query.toLocaleLowerCase('fr')))
    .sort((a, b) => sort === 'name' ? a.projet_nom.localeCompare(b.projet_nom, 'fr') : Number(b[sort] || 0) - Number(a[sort] || 0));
  const currentPage = Math.min(page, Math.max(1, Math.ceil(projects.length / 10)));
  const visible = projects.slice((currentPage - 1) * 10, currentPage * 10);
  const totals = report.totaux;
  return <TgmPanel title="Coût des projets et prestations" description={report.formule}>
    <TgmTableControls query={query} setQuery={setQuery} sort={sort} setSort={setSort} page={currentPage} setPage={setPage} count={projects.length}
      options={ [['name', 'Projet'], ['cout_calculable', 'Coût calculable décroissant'], ['heures_validees', 'Heures validées décroissantes']] } />
    {report.projets.length > 0 && !projects.length ? <p role="status">Aucun projet ne correspond à la recherche.</p> : null}
    {!report.projets.length ? <p role="status">Aucune heure validée sur un projet pendant cette période.</p> : <>
      <p className="tgm-note">{totals.heures_validees} heures validées · Coût calculable : <strong>{amount(totals.cout_calculable)}</strong> · Coût complet : <strong>{totals.cout_complet ? amount(totals.cout_estime) : 'Estimation incomplète'}</strong>.</p>
      {!totals.cout_complet && <p className="message-box" role="status">{totals.heures_sans_tgm} heures restent sans taux disponible. Le sous-total calculable ne représente pas le coût complet.</p>}
      <CostTable title="Synthèse par projet" label="Projet" rows={visible.map((project) => ({ ...project, id: project.projet_id, label: `${project.projet_code} · ${project.projet_nom}` }))} />
      {visible.map((project) => <details className="tgm-project" key={project.projet_id}>
        <summary>{project.projet_code} · {project.projet_nom} — détails des coûts</summary>
        <CostTable title={`Employés · ${project.projet_nom}`} label="Employé" rows={project.employes.map((row) => ({ ...row, id: row.employe_id, label: `${row.employe_prenom} ${row.employe_nom} · ${row.matricule}` }))} />
        <CostTable title={`Tâches · ${project.projet_nom}`} label="Tâche" rows={project.taches.map((row) => ({ ...row, id: row.tache_id, label: `${row.tache_code} · ${row.tache_nom}` }))} />
      </details>)}
    </>}
    <p className="tgm-note">{report.note}</p>
  </TgmPanel>;
}
