import React from 'react';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../../../shared/components/ui/table.jsx';
import { employeeFullName } from '../lib/projectAssignments.js';

export default function ProjectTaskTable({ tasks, assignments, canAssign, canDelete, busy, onAssign, onDelete }) {
  const names = new Map(assignments.map((item) => [Number(item.employe), employeeFullName(item)]));
  const assignedEmployeeName = (id) => names.get(Number(id)) || `Employé ${id}`;
  return <Table className="project-management-table" containerProps={{ tabIndex: 0, role: 'region', 'aria-label': 'Tâches et employés affectés' }}>
    <caption className="sr-only">Tâches du projet et employés autorisés à saisir leur temps.</caption>
    <TableHeader><TableRow><TableHead scope="col">Tâche</TableHead><TableHead scope="col" className="project-people-column">Employés affectés</TableHead>
      <TableHead scope="col" className="project-status">Statut</TableHead><TableHead scope="col" className="text-right">Actions</TableHead></TableRow></TableHeader>
    <TableBody>{tasks.map((task) => <TableRow key={task.id}>
      <TableHead scope="row" className="project-identity">{task.nom}<span className="project-mobile-people project-secondary">{task.actif ? 'Active' : 'Inactive'} · {task.employes?.length ? task.employes.map(assignedEmployeeName).join(', ') : 'À affecter'}</span></TableHead>
      <TableCell className="project-task-people project-people-column">{task.employes?.length
        ? <ul>{task.employes.map((id) => <li key={id}>{assignedEmployeeName(id)}</li>)}</ul>
        : <span className="project-unassigned">À affecter</span>}</TableCell>
      <TableCell className="project-status">{task.actif ? 'Active' : 'Inactive'}</TableCell>
      <TableCell><div className="project-row-actions">
        {canAssign && <button className="outline-button" type="button" disabled={busy} onClick={() => onAssign(task)} aria-label={`Modifier les affectations de ${task.nom}`}>Affectations</button>}
        {canDelete && <button className="danger-button" type="button" disabled={busy} onClick={() => onDelete(task)} aria-label={`Supprimer la tâche ${task.nom}`}>Supprimer</button>}
        {!canAssign && !canDelete && <span>—</span>}
      </div></TableCell>
    </TableRow>)}</TableBody>
  </Table>;
}
