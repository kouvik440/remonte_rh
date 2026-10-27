import React, { useState } from 'react';
import { hasPermission } from '../../../shared/lib/api.js';
import DeleteConfirmation from '../../../shared/components/DeleteConfirmation.jsx';
import useLeaveMutation from '../hooks/useLeaveMutation.js';
import LeaveField from './LeaveField.jsx';

const blankType = () => ({ libelle: '', jours_par_annee: 0, est_payant: true, actif: true });

/** @param {{ types: Array, onChanged: Function, loading: boolean }} props */
export default function LeaveTypeManager({ types, onChanged, loading }) {
  const [form, setForm] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const [success, setSuccess] = useState('');
  const mutation = useLeaveMutation(onChanged);
  const canCreate = hasPermission('conge.create');
  const canUpdate = hasPermission('conge.update');
  const canDelete = hasPermission('conge.delete');
  const openEditor = (type = null) => {
    mutation.reset();
    setSuccess('');
    setEditingId(type?.id ?? null);
    setForm(type ? { libelle: type.libelle, jours_par_annee: type.jours_par_annee, est_payant: type.est_payant, actif: type.actif } : blankType());
  };
  const save = async (event) => {
    event.preventDefault();
    if (editingId ? !canUpdate : !canCreate) return;
    const saved = await mutation.submit(editingId ? `/api/conges/types/${editingId}/` : '/api/conges/types/', editingId ? 'PUT' : 'POST', {
      ...form, jours_par_annee: Number(form.jours_par_annee),
    });
    if (saved) { setForm(null); setSuccess('Type de congé enregistré.'); }
  };
  const remove = async () => {
    if (!canDelete || !deleting) return;
    const removed = await mutation.submit(`/api/conges/types/${deleting.id}/`, 'DELETE');
    setDeleting(null);
    if (removed) { setForm(null); setSuccess('Type de congé supprimé.'); }
  };
  return <section className="content-card leave-management">
    <div className="card-heading"><h2>Types de congé</h2>
      {canCreate && <button type="button" className="primary-button" disabled={mutation.saving} onClick={() => openEditor()}>Créer un type</button>}
    </div>
    <p>Le droit annuel est commun à tous les employés. Toute modification recalcule leurs soldes. Le code est généré automatiquement.</p>
    {mutation.message && <p role="alert" className="message-box error">{mutation.message}</p>}
    {success && <p role="status" className="message-box success">{success}</p>}
    {deleting && <DeleteConfirmation description={`Supprimer le type « ${deleting.libelle} » ? Les types utilisés doivent être désactivés.`}
      busy={mutation.saving} onCancel={() => setDeleting(null)} onConfirm={remove} />}
    {form && <form onSubmit={save} aria-busy={mutation.saving}>
      <fieldset className="leave-form-grid" disabled={mutation.saving}>
        {['libelle', 'jours_par_annee'].map((field) => <LeaveField key={field}
          label={{ code: 'Code', libelle: 'Libellé', jours_par_annee: 'Droit annuel en jours' }[field]} error={mutation.errors[field]}>
          {(props) => <input {...props} type={field === 'jours_par_annee' ? 'number' : 'text'} min={field === 'jours_par_annee' ? 0 : undefined}
            maxLength={field === 'libelle' ? 100 : undefined} required value={form[field]}
            onChange={(event) => setForm({ ...form, [field]: event.target.value })} />}
        </LeaveField>)}
        <label><input type="checkbox" checked={form.est_payant} onChange={(event) => setForm({ ...form, est_payant: event.target.checked })} /> Congé payé</label>
        <label><input type="checkbox" checked={form.actif} onChange={(event) => setForm({ ...form, actif: event.target.checked })} /> Type actif</label>
      </fieldset>
      <div className="form-footer">
        <button type="button" className="outline-button" disabled={mutation.saving} onClick={() => setForm(null)}>Annuler</button>
        <button type="submit" className="primary-button" disabled={mutation.saving}>{mutation.saving ? 'Enregistrement…' : 'Enregistrer'}</button>
      </div>
    </form>}
    {loading ? <p role="status">Chargement des types de congé…</p> : types.length === 0 ? <p>Aucun type de congé.</p> : <div className="leave-type-list">{types.map((type) => <article className="leave-type-card" key={type.id}>
      <div><h3>{type.libelle}</h3><p>{type.jours_par_annee} jours/an · {type.est_payant ? 'Payé' : 'Non payé'} · {type.actif ? 'Actif' : 'Inactif'}</p></div>
      <div className="leave-request-actions">
        {canUpdate && <button type="button" className="outline-button" disabled={mutation.saving} onClick={() => openEditor(type)}>Modifier</button>}
        {canDelete && <button type="button" className="danger-button" disabled={mutation.saving} onClick={() => { mutation.reset(); setSuccess(''); setDeleting(type); }}>Supprimer</button>}
      </div>
    </article>)}</div>}
  </section>;
}
