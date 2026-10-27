import React, { useState } from 'react';
import FormField from '../../../shared/components/FormField.jsx';

/** @param {{ type: Object | null, mutation: Object, onClose: Function, onSaved: Function }} props */
export default function ContractTypeEditor({ type, mutation, onClose, onSaved }) {
  const [form, setForm] = useState({ type: type?.type || '', description: type?.description || '' });
  const save = async (event) => {
    event.preventDefault();
    if (await mutation.submit(type ? `/api/types-contrat/${type.id}/` : '/api/types-contrat/', type ? 'PUT' : 'POST', form)) onSaved();
  };
  return <form onSubmit={save}>
    <h3>{type ? 'Modifier le type de contrat' : 'Nouveau type de contrat'}</h3>
    <fieldset className="leave-form-grid" disabled={mutation.saving}>
      <FormField label="Libellé du type" error={mutation.errors.type}>{(a11y) => <input {...a11y} value={form.type} onChange={(event) => setForm((value) => ({ ...value, type: event.target.value }))} maxLength={100} required />}</FormField>
      <FormField label="Description (facultative)" error={mutation.errors.description}>{(a11y) => <textarea {...a11y} value={form.description} onChange={(event) => setForm((value) => ({ ...value, description: event.target.value }))} />}</FormField>
    </fieldset>
    {mutation.message && <p className="message-box error" role="alert">{mutation.message}</p>}
    <div className="form-footer"><button type="button" className="outline-button" onClick={onClose} disabled={mutation.saving}>Annuler la saisie</button><button type="submit" className="primary-button" disabled={mutation.saving}>{mutation.saving ? 'Enregistrement…' : 'Enregistrer le type'}</button></div>
  </form>;
}
