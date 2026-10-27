import React, { useState } from 'react';
import DeleteConfirmation from '../../../shared/components/DeleteConfirmation.jsx';
import { hasPermission } from '../../../shared/lib/api.js';
import useApiMutation from '../../../shared/hooks/useApiMutation.js';
import { canAct, fieldsFor, formFor, payloadFor, resources } from '../lib/resources.js';
import RecordEditor from './RecordEditor.jsx';
import RecordSummary from './RecordSummary.jsx';

/** @param {{ kind: string, records: Array, employees: Array, loading: boolean, error: string, onChanged: Function }} props */
export default function RecordManager({ kind, records, employees, loading, error, onChanged }) {
  const [form, setForm] = useState(null);
  const [editing, setEditing] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const [success, setSuccess] = useState('');
  const mutation = useApiMutation(onChanged);
  const fields = fieldsFor(kind, { employees }, editing !== null);
  const needsEmployees = hasPermission('coordonnees_bancaires.manage');
  const canSelect = !needsEmployees || (hasPermission('employe.read') && employees.length > 0);
  const ready = canSelect;
  const open = (record = null) => {
    mutation.reset(); setSuccess(''); setEditing(record?.id ?? null);
    setForm(formFor(fieldsFor(kind, { employees }, record !== null), record));
  };
  const save = async (event) => {
    event.preventDefault();
    if (!canAct(kind, editing !== null ? 'update' : 'create')) return;
    const saved = await mutation.submit(editing !== null ? `${resources[kind].path}${editing}/` : resources[kind].path,
      editing !== null ? 'PUT' : 'POST', payloadFor(fields, form));
    if (saved) { setForm(null); setSuccess('Enregistrement effectué.'); }
  };
  const remove = async () => {
    if (!canAct(kind, 'delete') || !deleting) return;
    const removed = await mutation.submit(`${resources[kind].path}${deleting.id}/`, 'DELETE');
    setDeleting(null);
    if (removed) { setForm(null); setSuccess('Suppression effectuée.'); }
  };
  return <section className="content-card module-three-panel">
    <div className="card-heading"><h2>{resources[kind].title}</h2><div className="leave-request-actions">
      <button type="button" className="outline-button" disabled={loading || mutation.saving} onClick={onChanged}>Actualiser</button>
      {canAct(kind, 'create') && <button type="button" className="primary-button" disabled={!ready || loading || mutation.saving} onClick={() => open()}>Ajouter</button>}
    </div></div>
    {canAct(kind, 'create') && !ready && !loading && <p role="status">Pour ajouter une fiche, la liste des employés doit être accessible et renseignée.</p>}
    {error && <p className="message-box error" role="alert">{error}</p>}
    {mutation.message && <p className="message-box error" role="alert">{mutation.message}</p>}
    {success && <p className="message-box success" role="status">{success}</p>}
    {form && <>
      <RecordEditor fields={fields} form={form} setForm={setForm} mutation={mutation} onSave={save} onCancel={() => setForm(null)} />
    </>}
    {deleting && <DeleteConfirmation description={`Supprimer cette fiche bancaire ? Cette action est définitive.`}
      busy={mutation.saving} onCancel={() => setDeleting(null)} onConfirm={remove} />}
    {loading ? <p role="status">Chargement…</p> : !error && (records.length === 0 ? <p>Aucun enregistrement accessible.</p> : <div className="module-three-records">
      {records.map((record) => <article key={record.id} className="module-three-record">
        <RecordSummary record={record} />
        <div className="leave-request-actions">
          {canAct(kind, 'update') && <button type="button" className="outline-button" disabled={mutation.saving} onClick={() => open(record)}>Modifier</button>}
          {canAct(kind, 'delete') && <button type="button" className="danger-button" disabled={mutation.saving} onClick={() => { mutation.reset(); setSuccess(''); setDeleting(record); }}>Supprimer</button>}
        </div>
      </article>)}
    </div>)}
  </section>;
}
