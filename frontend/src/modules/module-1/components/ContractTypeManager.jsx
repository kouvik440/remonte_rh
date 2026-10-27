import React, { useState } from 'react';
import ModalDialog from '../../../shared/components/ModalDialog.jsx';
import useApiMutation from '../../../shared/hooks/useApiMutation.js';
import { hasPermission } from '../../../shared/lib/api.js';
import useContractTypes from '../hooks/useContractTypes.js';
import ContractTypeEditor from './ContractTypeEditor.jsx';

/** @param {{ onClose: Function, onChanged?: Function }} props */
export default function ContractTypeManager({ onClose, onChanged }) {
  const data = useContractTypes();
  const mutation = useApiMutation(async () => { await data.load(); if (onChanged) await onChanged(); });
  const [editor, setEditor] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const [notice, setNotice] = useState('');
  const open = (type) => { mutation.reset(); setNotice(''); setEditor({ type }); };
  const remove = async () => {
    if (await mutation.submit(`/api/types-contrat/${deleting.id}/`, 'DELETE')) { setDeleting(null); setNotice('Type de contrat supprimé.'); }
  };
  return <ModalDialog title="Types de contrat" busy={mutation.saving} onClose={onClose}>
    <p>Définissez les types qui seront proposés dans les contrats des employés. Un type utilisé par un contrat reste protégé contre la suppression.</p>
    {notice && <p className="message-box" role="status">{notice}</p>}
    {editor ? <ContractTypeEditor key={editor.type?.id || 'new'} type={editor.type} mutation={mutation} onClose={() => setEditor(null)} onSaved={() => { setEditor(null); setNotice('Type de contrat enregistré.'); }} />
      : deleting ? <section className="message-box" role="alert"><h3>Supprimer « {deleting.type} » ?</h3>
        {mutation.message && <p className="field-error">{mutation.message}</p>}
        <div className="form-footer"><button type="button" className="outline-button" disabled={mutation.saving} onClick={() => setDeleting(null)}>Conserver</button><button type="button" className="danger-button" disabled={mutation.saving} onClick={remove}>Confirmer la suppression</button></div>
      </section> : <>
        <div className="form-footer"><button type="button" className="outline-button" disabled={data.loading || mutation.saving} onClick={data.load}>Actualiser</button>
          {hasPermission('type_contrat.create') && <button type="button" className="primary-button" disabled={data.loading || mutation.saving} onClick={() => open(null)}>Nouveau type</button>}</div>
        {data.loading ? <p role="status">Chargement des types…</p> : data.error ? <p className="message-box error" role="alert">{data.error}</p>
          : <ContractTypeList types={data.types} onEdit={open} onDelete={(type) => { mutation.reset(); setDeleting(type); }} busy={mutation.saving} />}
      </>}
    <div className="form-footer"><button type="button" className="outline-button" disabled={mutation.saving} onClick={onClose}>Fermer</button></div>
  </ModalDialog>;
}

export function ContractTypeList({ types, onEdit, onDelete, busy }) {
  if (!types.length) return <p>Aucun type de contrat enregistré.</p>;
  return <div className="contract-list">{types.map((type) => <article key={type.id} className="leave-request-card payroll-card">
    <div className="leave-request-main"><h3>{type.type}</h3><p>{type.description || 'Aucune description'}</p></div>
    <div className="leave-request-actions">
      {hasPermission('type_contrat.update') && <button type="button" className="outline-button" disabled={busy} onClick={() => onEdit(type)}>Modifier</button>}
      {hasPermission('type_contrat.delete') && <button type="button" className="danger-button" disabled={busy} onClick={() => onDelete(type)}>Supprimer</button>}
    </div>
  </article>)}</div>;
}
