import React from 'react';
import { hasPermission } from '../../../shared/lib/api.js';

/** @param {{ departments: Array, busy: boolean, onEdit: Function, onDelete: Function }} props */
export default function DepartmentList({ departments, busy, onEdit, onDelete }) {
  if (!departments.length) return <p className="leave-state">Aucun département enregistré.</p>;
  return <div className="contract-list">{departments.map((department) =>
    <article key={department.id} className="leave-request-card payroll-card">
      <div className="leave-request-main"><h3>{department.nom}</h3></div>
      <div className="leave-request-actions">
        {hasPermission('departement.update') && <button type="button" className="outline-button" disabled={busy} onClick={() => onEdit(department)}>Modifier</button>}
        {hasPermission('departement.delete') && <button type="button" className="danger-button" disabled={busy} onClick={() => onDelete(department)}>Supprimer</button>}
      </div>
    </article>)}</div>;
}
