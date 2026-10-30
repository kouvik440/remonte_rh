import React, { useState } from 'react';
import ModalDialog from '../../../shared/components/ModalDialog.jsx';
import useApiResource from '../../../shared/hooks/useApiResource.js';
import { hasPermission } from '../../../shared/lib/api.js';
import ProjectTaskTable from './ProjectTaskTable.jsx';
import useTimesheetMutation from '../hooks/useTimesheetMutation.js';
import ProjectNameForm from './ProjectNameForm.jsx';
import ResourceState from './ResourceState.jsx';
import { employeeAssignmentOption } from '../lib/projectAssignments.js';

export default function ProjectDetails({ project }) {
  const canReadTasks = hasPermission('tache.read');
  const canAssign = hasPermission('projet.assign_employees');
  const canReadEmployees = hasPermission('employe.read');
  const base = `/api/projets/${project.id}/`;
  const tasks = useApiResource(`${base}taches/`, canReadTasks);
  const assignments = useApiResource(`${base}affectations/`);
  const employees = useApiResource('/api/employes/', canAssign && canReadEmployees);
  const mutation = useTimesheetMutation();
  const [newTask, setNewTask] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  const [removing, setRemoving] = useState(null);
  const [deletingTask, setDeletingTask] = useState(null);
  const [notice, setNotice] = useState('');
  const employeeOptions = canReadEmployees
    ? (employees.report || []).filter((item) => item.is_active || editingTask?.employes?.includes(item.id)).map(employeeAssignmentOption)
    : assignments.report || [];
  const optionsReady = !assignments.loading && !assignments.error && (!canReadEmployees || (!employees.loading && !employees.error));
  function taskSaved(result) {
    setNewTask(false); setEditingTask(null); tasks.reload(); assignments.reload();
    setNotice(`${result.nom} : ${result.employes.length} employé(s) affecté(s). Affectations enregistrées.`);
  }
  return <section className="timesheet-project-detail" aria-label={`Tâches de ${project.nom}`}>
    <div className="project-detail-heading"><div><h3>{project.nom}</h3><p className="project-secondary">Les employés choisis pour une tâche rejoignent automatiquement le projet.</p></div>
      {hasPermission('tache.create') && <button className="primary-button" type="button" disabled={mutation.busy || (canAssign && !optionsReady)} onClick={() => { mutation.reset(); setNotice(''); setNewTask(true); }}>Nouvelle tâche</button>}</div>
    {!project.actif && <p className="message-box">Ce projet est inactif : il n’est pas proposé pour de nouvelles saisies.</p>}
    {notice && <p className="message-box success" role="status">{notice}</p>}
    {canAssign && canReadEmployees && employees.error && <ResourceState data={employees} label="des employés" />}
    <ResourceState data={assignments} label="des affectations">{(members) => <>
      {canReadTasks ? <ResourceState data={tasks} label="des tâches">{(items) => items.length
        ? <ProjectTaskTable tasks={items} assignments={members} canAssign={canAssign} canDelete={hasPermission('tache.delete')} busy={mutation.busy || !optionsReady} onAssign={(task) => { mutation.reset(); setEditingTask(task); }} onDelete={(task) => { mutation.reset(); setDeletingTask(task); }} />
        : <p className="project-empty" role="status">Aucune tâche dans ce projet. Ajoutez une tâche et choisissez directement ses employés.</p>}</ResourceState>
        : <p>La consultation des tâches nécessite le droit tache.read.</p>}
      <details className="project-team"><summary>Équipe du projet · {members.length} employé{members.length > 1 ? 's' : ''}</summary>
        <p className="project-secondary">L’appartenance au projet ne donne accès qu’aux tâches attribuées.</p>
        {!members.length ? <p>Aucun employé pour le moment.</p> : <ul className="timesheet-simple-list">{members.map((item) => <li key={item.id}>
          <span>{item.employe_prenom} {item.employe_nom} · {item.employe_matricule}</span>
          {canAssign && <button className="danger-button" type="button" disabled={mutation.busy} onClick={() => { mutation.reset(); setRemoving(item); }}>Retirer du projet</button>}
        </li>)}</ul>}
      </details>
    </>}</ResourceState>
    {!newTask && !editingTask && !removing && !deletingTask && mutation.error && <p className="message-box error" role="alert">{mutation.error}</p>}
    {deletingTask && <ModalDialog title="Supprimer une tâche" busy={mutation.busy} onClose={() => setDeletingTask(null)}>
      <p>Supprimer la tâche {deletingTask.nom} ? Une tâche déjà utilisée dans une feuille de temps sera conservée.</p>
      {mutation.error && <p className="message-box error" role="alert">{mutation.error}</p>}
      <div className="form-footer"><button className="outline-button" type="button" disabled={mutation.busy} onClick={() => setDeletingTask(null)}>Annuler</button>
        <button className="danger-button" type="button" disabled={mutation.busy} onClick={() => mutation.run(`${base}taches/${deletingTask.id}/`, 'DELETE', undefined, () => { setDeletingTask(null); tasks.reload(); setNotice('Tâche supprimée.'); })}>Confirmer la suppression</button></div>
    </ModalDialog>}
    {editingTask && <ProjectNameForm title="Modifier les affectations" task={editingTask} assignments={employeeOptions} path={`${base}taches/${editingTask.id}/`} mutation={mutation} onClose={() => setEditingTask(null)} onSaved={taskSaved} />}
    {newTask && <ProjectNameForm assignments={canAssign ? employeeOptions : undefined} title="Nouvelle tâche" path={`${base}taches/`} mutation={mutation} onClose={() => setNewTask(false)} onSaved={taskSaved} />}
    {removing && <ModalDialog title="Retirer du projet" busy={mutation.busy} onClose={() => setRemoving(null)}>
      <p>Retirer {removing.employe_prenom} {removing.employe_nom} du projet et de ses tâches ? Ses lignes enregistrées seront conservées.</p>
      {mutation.error && <p className="message-box error" role="alert">{mutation.error}</p>}
      <div className="form-footer"><button className="outline-button" type="button" disabled={mutation.busy} onClick={() => setRemoving(null)}>Annuler</button>
        <button className="danger-button" type="button" disabled={mutation.busy} onClick={() => mutation.run(`${base}affectations/${removing.employe}/`, 'DELETE', undefined, () => { setRemoving(null); assignments.reload(); tasks.reload(); setNotice('Employé retiré du projet et de ses tâches.'); })}>Confirmer le retrait</button></div>
    </ModalDialog>}
  </section>;
}
