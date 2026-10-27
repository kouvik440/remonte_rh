import React, { useState } from 'react';
import ModalDialog from '../../../shared/components/ModalDialog.jsx';
import Field from './TimesheetField.jsx';

export default function ProjectNameForm({ title, path, mutation, onClose, onSaved }) {
  const [name, setName] = useState('');
  const [errors, setErrors] = useState({});
  function save(event) {
    event.preventDefault();
    const next = {};
    if (!name.trim()) next.name = 'Le nom est obligatoire.';
    setErrors(next);
    if (Object.keys(next).length) return;
    mutation.run(path, 'POST', { nom: name.trim(), actif: true }, onSaved);
  }
  return <ModalDialog title={title} busy={mutation.busy} onClose={onClose}>
    <form onSubmit={save} noValidate>
      <Field label="Nom" error={errors.name}><input value={name} maxLength={150} required disabled={mutation.busy} onChange={(event) => setName(event.target.value)} /></Field>
      {mutation.error && <p className="message-box error" role="alert">{mutation.error}</p>}
      <div className="form-footer"><button className="outline-button" type="button" disabled={mutation.busy} onClick={onClose}>Annuler</button>
        <button className="primary-button" type="submit" disabled={mutation.busy}>Enregistrer</button></div>
    </form>
  </ModalDialog>;
}
