import React, { useId, useState } from 'react';
import Field from './TimesheetField.jsx';
import { employeeFullName, matchesSearch } from '../lib/projectAssignments.js';

export default function TaskEmployeePicker({ employees, selected, onChange, disabled, error }) {
  const [search, setSearch] = useState('');
  const hintId = useId();
  const errorId = useId();
  const visibleEmployees = employees.filter((employee) => matchesSearch(`${employeeFullName(employee)} ${employee.employe_matricule}`, search));

  function toggleEmployee(employeeId, checked) {
    onChange(checked ? [...selected, employeeId] : selected.filter((id) => id !== employeeId));
  }

  return <fieldset className="task-employee-picker" disabled={disabled} aria-describedby={error ? errorId : hintId}>
    <legend>Employés affectés à cette tâche</legend>
    <p id={hintId} className="project-secondary">L’affectation au projet est incluse. Aucun second enregistrement nécessaire.</p>
    <Field label="Rechercher un employé"><input type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Nom ou matricule" /></Field>
    {!employees.length && <p>Aucun employé disponible.</p>}
    <div className="task-employee-options">{visibleEmployees.map((employee) => <label key={employee.employe} className="task-employee-option">
      <input type="checkbox" checked={selected.includes(employee.employe)} onChange={(event) => toggleEmployee(employee.employe, event.target.checked)} />
      <span>{employeeFullName(employee)}<small>{employee.employe_matricule}</small></span>
    </label>)}</div>
    {search && !visibleEmployees.length && <p role="status">Aucun employé ne correspond à votre recherche.</p>}
    <p role="status">{selected.length} employé{selected.length > 1 ? 's' : ''} sélectionné{selected.length > 1 ? 's' : ''}</p>
    {error && <p id={errorId} className="field-error" role="alert">{error}</p>}
  </fieldset>;
}
