import React, { useState } from 'react';
import ModalDialog from '../../../shared/components/ModalDialog.jsx';
import useApiResource from '../../../shared/hooks/useApiResource.js';
import { hasPermission } from '../../../shared/lib/api.js';
import useTimesheetMutation from '../hooks/useTimesheetMutation.js';
import ProjectNameForm from './ProjectNameForm.jsx';
import Field from './TimesheetField.jsx';
import ResourceState from './ResourceState.jsx';

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
  const [employee, setEmployee] = useState('');
  const [employeeError, setEmployeeError] = useState('');
  const [removing, setRemoving] = useState(null);
  const [deletingTask, setDeletingTask] = useState(null);
  const [notice, setNotice] = useState('');
  function assign(event) {
    event.preventDefault();
    if (!canAssign || !canReadEmployees) return;
    if (!(employees.report || []).some((item) => String(item.id) === employee)) { setEmployeeError('Choisissez un employé.'); return; }
    setEmployeeError(''); setNotice('');
    mutation.run(`${base}affectations/`, 'POST', { employe: Number(employee) }, () => { setEmployee(''); setNotice('Employé affecté au projet. Il pourra le sélectionner dans ses feuilles de temps.'); assignments.reload(); });
  }
  return <div className="timesheet-project-detail">
    <h3>{project.nom}</h3>
    {!project.actif && <p className="message-box">Ce projet est inactif : il n’est pas proposé pour de nouvelles saisies.</p>}
    {notice && <p className="message-box success" role="status">{notice}</p>}
    <div className="timesheet-project-columns">
      <section><h4>Tâches du projet</h4>
        {canReadTasks ? <ResourceState data={tasks} label="des tâches">{(items) => !items.length ? <p>Aucune tâche. Ajoutez-en une pour permettre la saisie du temps.</p> : <ul className="timesheet-simple-list">{items.map((task) => <li key={task.id}>
          <span>{task.nom} {!task.actif && '(inactive)'}</span>
          {hasPermission('tache.delete') && <button className="danger-button" type="button" disabled={mutation.busy} onClick={() => { mutation.reset(); setDeletingTask(task); }}>Supprimer la tâche {task.nom}</button>}
        </li>)}</ul>}</ResourceState>
          : <p>La consultation des tâches nécessite le droit tache.read.</p>}
        {hasPermission('tache.create') && <button className="outline-button" type="button" disabled={mutation.busy} onClick={() => { mutation.reset(); setNewTask(true); }}>Nouvelle tâche</button>}
      </section>
      <section><h4>Employés affectés</h4>
        <p className="timesheet-note">Les employés affectés accèdent à toutes les tâches actives de ce projet.</p>
        <ResourceState data={assignments} label="des affectations">{(items) => !items.length ? <p>Aucun employé affecté à ce projet.</p> : <ul className="timesheet-simple-list">{items.map((item) => <li key={item.id}>
          <span>{item.employe_prenom} {item.employe_nom} · {item.employe_matricule}</span>
          {canAssign && <button className="danger-button" type="button" disabled={mutation.busy} onClick={() => { mutation.reset(); setRemoving(item); }}>Retirer l’affectation de {item.employe_prenom}</button>}
        </li>)}</ul>}</ResourceState>
        {canAssign && canReadEmployees && <ResourceState data={employees} label="des employés">{(items) => <form onSubmit={assign} noValidate className="timesheet-assignment-form">
          <Field label="Employé à affecter" error={employeeError}><select value={employee} required disabled={mutation.busy} onChange={(event) => setEmployee(event.target.value)}>
            <option value="">Choisir un employé</option>
            {items.filter((item) => item.is_active && !(assignments.report || []).some((assignment) => String(assignment.employe) === String(item.id))).map((item) => <option key={item.id} value={item.id}>{item.prenom} {item.nom} · {item.matricule}</option>)}
          </select></Field>
          <button className="primary-button" type="submit" disabled={mutation.busy || assignments.loading || Boolean(assignments.error)}>Affecter au projet</button>
        </form>}</ResourceState>}
        {canAssign && !canReadEmployees && <p>Le sélecteur d’employés nécessite aussi employe.read.</p>}
      </section>
    </div>
    {!newTask && !removing && !deletingTask && mutation.error && <p className="message-box error" role="alert">{mutation.error}</p>}
    {deletingTask && <ModalDialog title="Supprimer une tâche" busy={mutation.busy} onClose={() => setDeletingTask(null)}>
      <p>Supprimer la tâche {deletingTask.nom} ? Une tâche déjà utilisée dans une feuille de temps sera conservée.</p>
      {mutation.error && <p className="message-box error" role="alert">{mutation.error}</p>}
      <div className="form-footer"><button className="outline-button" type="button" disabled={mutation.busy} onClick={() => setDeletingTask(null)}>Annuler</button>
        <button className="danger-button" type="button" disabled={mutation.busy} onClick={() => mutation.run(`${base}taches/${deletingTask.id}/`, 'DELETE', undefined, () => { setDeletingTask(null); tasks.reload(); setNotice('Tâche supprimée.'); })}>Confirmer la suppression</button></div>
    </ModalDialog>}
    {newTask && <ProjectNameForm title="Nouvelle tâche" path={`${base}taches/`} mutation={mutation} onClose={() => setNewTask(false)} onSaved={() => { setNewTask(false); setNotice('Tâche créée.'); tasks.reload(); }} />}
    {removing && <ModalDialog title="Retirer une affectation" busy={mutation.busy} onClose={() => setRemoving(null)}>
      <p>Retirer {removing.employe_prenom} {removing.employe_nom} du projet ? Ses lignes enregistrées seront conservées, mais il ne pourra plus saisir ou soumettre de temps pour ce projet.</p>
      {mutation.error && <p className="message-box error" role="alert">{mutation.error}</p>}
      <div className="form-footer"><button className="outline-button" type="button" disabled={mutation.busy} onClick={() => setRemoving(null)}>Annuler</button>
        <button className="danger-button" type="button" disabled={mutation.busy} onClick={() => mutation.run(`${base}affectations/${removing.employe}/`, 'DELETE', undefined, () => { setRemoving(null); assignments.reload(); setNotice('Affectation retirée.'); })}>Confirmer le retrait</button></div>
    </ModalDialog>}
  </div>;
}
