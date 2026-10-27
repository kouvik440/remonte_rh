import React, { useState } from 'react';
import ModalDialog from '../../../shared/components/ModalDialog.jsx';
import FormField from '../../../shared/components/FormField.jsx';
import useApiResource from '../../../shared/hooks/useApiResource.js';
import useApiMutation from '../../../shared/hooks/useApiMutation.js';
import { hasPermission } from '../../../shared/lib/api.js';

export default function PositionManager({ onClose, onChanged }) {
  const data = useApiResource('/api/postes/');
  const mutation = useApiMutation(async () => { data.reload(); await onChanged?.(); });
  const [editor, setEditor] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const [notice, setNotice] = useState('');
  function edit(position) { mutation.reset(); setNotice(''); setEditor({ position }); }
  async function remove() {
    if (await mutation.submit(`/api/postes/${deleting.id}/`, 'DELETE')) { setDeleting(null); setNotice('Poste supprimé.'); }
  }
  return <ModalDialog title="Catalogue des postes" busy={mutation.saving} onClose={onClose}>
    <p>Créez les postes qui seront proposés dans les contrats. Un même poste peut être utilisé pour plusieurs employés. Les postes liés à un contrat sont protégés contre la suppression.</p>
    {notice && <p className="message-box success" role="status">{notice}</p>}
    {editor ? <PositionEditor key={editor.position?.id || 'new'} position={editor.position} mutation={mutation} onClose={() => setEditor(null)} onSaved={() => { setEditor(null); setNotice('Poste enregistré.'); }} />
      : deleting ? <section role="alert"><h3>Supprimer le poste « {deleting.nom} » ?</h3>
        {mutation.message && <p className="message-box error">{mutation.message}</p>}
        <div className="form-footer"><button type="button" className="outline-button" disabled={mutation.saving} onClick={() => setDeleting(null)}>Conserver</button>
          <button type="button" className="danger-button" disabled={mutation.saving} onClick={remove}>Confirmer la suppression</button></div>
      </section> : <>
        <div className="form-footer"><button type="button" className="outline-button" disabled={data.loading || mutation.saving} onClick={data.reload}>Actualiser les postes</button>
          {hasPermission('poste.create') && <button type="button" className="primary-button" disabled={mutation.saving} onClick={() => edit(null)}>Nouveau poste</button>}</div>
        {data.loading ? <p role="status">Chargement des postes…</p> : data.error ? <p className="message-box error" role="alert">{data.error}</p>
          : !(data.report || []).length ? <p>Aucun poste enregistré.</p> : <div className="contract-list">{data.report.map((position) => <article className="leave-request-card position-catalogue-card" key={position.id}>
            <div className="leave-request-main"><h3>{position.nom}</h3><p>{position.description || 'Aucune description'}</p></div>
            <div className="leave-request-actions">
              {hasPermission('poste.update') && <button type="button" className="outline-button" aria-label={`Modifier le poste ${position.nom}`} disabled={mutation.saving} onClick={() => edit(position)}>Modifier</button>}
              {hasPermission('poste.delete') && <button type="button" className="danger-button" aria-label={`Supprimer le poste ${position.nom}`} disabled={mutation.saving} onClick={() => { mutation.reset(); setDeleting(position); }}>Supprimer</button>}
            </div></article>)}</div>}
      </>}
    <div className="form-footer"><button type="button" className="outline-button" disabled={mutation.saving} onClick={onClose}>Fermer</button></div>
  </ModalDialog>;
}

function PositionEditor({ position, mutation, onClose, onSaved }) {
  const [name, setName] = useState(position?.nom || '');
  const [description, setDescription] = useState(position?.description || '');
  async function save(event) {
    event.preventDefault();
    if (await mutation.submit(position ? `/api/postes/${position.id}/` : '/api/postes/', position ? 'PUT' : 'POST', { nom: name.trim(), description: description.trim() })) onSaved();
  }
  return <form onSubmit={save} aria-busy={mutation.saving}>
    <h3>{position ? 'Modifier un poste' : 'Nouveau poste'}</h3>
    <fieldset className="leave-form-grid" disabled={mutation.saving}>
      <FormField label="Nom du poste" error={mutation.errors.nom}>{(props) => <input {...props} aria-label="Nom du poste" required maxLength={150} value={name} onChange={(event) => setName(event.target.value)} />}</FormField>
      <FormField label="Description" error={mutation.errors.description}>{(props) => <textarea {...props} aria-label="Description du poste" value={description} rows="3" onChange={(event) => setDescription(event.target.value)} />}</FormField>
    </fieldset>
    {mutation.message && <p className="message-box error" role="alert">{mutation.message}</p>}
    <div className="form-footer"><button type="button" className="outline-button" disabled={mutation.saving} onClick={onClose}>Annuler</button>
      <button type="submit" className="primary-button" disabled={mutation.saving}>Enregistrer le poste</button></div>
  </form>;
}
