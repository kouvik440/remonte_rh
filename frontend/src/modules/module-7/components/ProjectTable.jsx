import React from 'react';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../../../shared/components/ui/table.jsx';

const displayDate = (value) => value ? value.split('-').reverse().join('/') : '—';

export default function ProjectTable({ projects, selected, onSelect }) {
  return <Table className="project-management-table" containerProps={{ tabIndex: 0, role: 'region', 'aria-label': 'Projets et prestations' }}>
    <caption className="sr-only">Projets et prestations : période, statut et gestion des tâches.</caption>
    <TableHeader><TableRow><TableHead scope="col">Projet</TableHead><TableHead scope="col" className="project-period">Période</TableHead>
      <TableHead scope="col" className="project-status">Statut</TableHead><TableHead scope="col" className="text-right">Actions</TableHead></TableRow></TableHeader>
    <TableBody>{projects.map((project) => <TableRow key={project.id} data-state={selected === String(project.id) ? 'selected' : undefined}>
      <TableHead scope="row" className="project-identity"><span>{project.nom}</span>
        {project.description && <small>{project.description}</small>}<small className="project-mobile-people">{project.actif ? 'Actif' : 'Inactif'} · {displayDate(project.date_debut)} / {displayDate(project.date_fin)}</small></TableHead>
      <TableCell className="tabular-nums project-period"><span>{displayDate(project.date_debut)}</span><span className="project-secondary">{displayDate(project.date_fin)}</span></TableCell>
      <TableCell className="project-status"><span className={`status-badge ${project.actif ? 'status-active' : 'status-suspended'}`}>{project.actif ? 'Actif' : 'Inactif'}</span></TableCell>
      <TableCell className="text-right"><button type="button" className="outline-button" aria-expanded={selected === String(project.id)} aria-controls="selected-project-details"
        onClick={() => onSelect(selected === String(project.id) ? '' : String(project.id))} aria-label={`Gérer les tâches de ${project.nom}`}>
        {selected === String(project.id) ? 'Fermer' : 'Gérer les tâches'}</button></TableCell>
    </TableRow>)}</TableBody>
  </Table>;
}
