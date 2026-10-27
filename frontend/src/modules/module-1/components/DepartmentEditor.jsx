import React, { useState } from 'react';
import FormField from '../../../shared/components/FormField.jsx';
import ModalDialog from '../../../shared/components/ModalDialog.jsx';
import { hasPermission } from '../../../shared/lib/api.js';

/** @param {{ department: Object | null, mutation: Object, onClose: Function, onSaved: Function }} props */
export default function DepartmentEditor({ department, mutation, onClose, onSaved }) {
  const [name, setName] = useState(department?.nom || '');
  const save = async (event) => {
    event.preventDefault();
    if (!hasPermission(department ? 'departement.update' : 'departement.create')) return;
    const path = department ? `/api/departements/${department.id}/` : '/api/departements/';
    const payload = { nom: name.trim() };
    if (await mutation.submit(path, department ? 'PUT' : 'POST', payload)) onSaved();
  };
  return <ModalDialog title={department ? 'Modifier le département' : 'Nouveau département'} busy={mutation.saving} onClose={onClose}>
    <form onSubmit={save} aria-busy={mutation.saving}>
      <fieldset className="department-form-fields" disabled={mutation.saving}>
        <FormField label="Nom du département" error={mutation.errors.nom}>{(a11y) =>
          <input {...a11y} value={name} onChange={(event) => setName(event.target.value)} maxLength={100} required />}</FormField>
      </fieldset>
      {mutation.message && <p className="message-box error" role="alert">{mutation.message}</p>}
      <div className="form-footer">
        <button type="button" className="outline-button" disabled={mutation.saving} onClick={onClose}>Annuler</button>
        <button type="submit" className="primary-button" disabled={mutation.saving}>{mutation.saving ? 'Enregistrement…' : 'Enregistrer'}</button>
      </div>
    </form>
  </ModalDialog>;
}
