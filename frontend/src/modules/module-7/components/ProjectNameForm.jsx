import React, { useState } from 'react';
import ModalDialog from '../../../shared/components/ModalDialog.jsx';
import Field from './TimesheetField.jsx';
import TaskEmployeePicker from './TaskEmployeePicker.jsx';

export default function ProjectNameForm({ title, path, mutation, onClose, onSaved, task, assignments }) {
  const [name, setName] = useState(task?.nom || '');
  const [selected, setSelected] = useState(task?.employes || []);
  const [errors, setErrors] = useState({});
  function save(event) {
    event.preventDefault();
    const next = {};
    if (!task && !name.trim()) next.name = 'Le nom est obligatoire.';
    if (!task && assignments !== undefined && !selected.length) next.employees = 'Choisissez au moins un employé pour cette tâche.';
    setErrors(next);
    if (Object.keys(next).length) return;
    mutation.run(path, task ? 'PATCH' : 'POST', task ? { employes: selected } : { nom: name.trim(), actif: true,
      ...(assignments !== undefined ? { employes: selected } : {}) }, onSaved);
  }
  return <ModalDialog title={title} busy={mutation.busy} onClose={onClose}>
    <form onSubmit={save} noValidate>
      {task ? <p>{task.nom}</p> : <Field label="Nom" error={errors.name}><input value={name} maxLength={150} required disabled={mutation.busy} onChange={(event) => { setName(event.target.value); setErrors((current) => ({ ...current, name: undefined })); }} /></Field>}
      {assignments !== undefined && <TaskEmployeePicker employees={assignments} selected={selected} disabled={mutation.busy} error={errors.employees}
        onChange={(employees) => { setSelected(employees); setErrors((current) => ({ ...current, employees: undefined })); }} />}
      {mutation.error && <p className="message-box error" role="alert">{mutation.error}</p>}
      <div className="form-footer"><button className="outline-button" type="button" disabled={mutation.busy} onClick={onClose}>Annuler</button>
        <button className="primary-button" type="submit" disabled={mutation.busy}>{mutation.busy ? 'Enregistrement…' : assignments !== undefined && !task ? 'Créer et affecter la tâche' : 'Enregistrer'}</button></div>
    </form>
  </ModalDialog>;
}
