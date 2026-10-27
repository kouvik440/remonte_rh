import React, { useState } from 'react';
import FormField from '../../../shared/components/FormField.jsx';

export const contractStatuses = { EN_COURS: 'En cours', CLOS: 'Clos', RESILIE: 'Résilié' };

/** @param {{ contract: Object | null, employeeId: number | string, types: Array, canChooseTypes: boolean, mutation: Object, onClose: Function, onSaved: Function }} props */
export default function ContractEditor({ contract, employeeId, types, positions = [], canChoosePosition, positionsLoading, positionsError, canChooseTypes, mutation, onClose, onSaved }) {
  const [form, setForm] = useState({ date_debut: contract?.date_debut || '', date_fin: contract?.date_fin || '',
    salaire_base: contract?.salaire_base ?? '', heures_journalieres: contract?.heures_journalieres ?? '',
    statut: contract?.statut || 'EN_COURS', type: (contract?.type || []).map(String), poste: contract?.poste ? String(contract.poste) : '' });
  const change = (key) => (event) => setForm((value) => ({ ...value, [key]: event.target.value }));
  const save = async (event) => {
    event.preventDefault();
    const payload = { ...form, date_fin: form.date_fin || null, employe: Number(employeeId), type: form.type.map(Number) };
    if (canChoosePosition) payload.poste = form.poste ? Number(form.poste) : null;
    else delete payload.poste;
    if (await mutation.submit(contract ? `/api/contrats/${contract.id}/` : '/api/contrats/', contract ? 'PUT' : 'POST', payload)) onSaved();
  };
  return <form onSubmit={save} className="contract-editor">
    <h3>{contract ? 'Modifier le contrat' : 'Nouveau contrat'}</h3>
    <fieldset className="leave-form-grid" disabled={mutation.saving}>
      <FormField label="Poste occupé" error={mutation.errors.poste}>{(a11y) => canChoosePosition
        ? <select {...a11y} aria-label="Poste occupé" required value={form.poste} disabled={positionsLoading || Boolean(positionsError)} onChange={change('poste')}>
          <option value="">Choisir un poste</option>{positions.map((position) => <option key={position.id} value={position.id}>{position.nom}</option>)}
        </select> : <input {...a11y} aria-label="Poste occupé" readOnly value={contract?.poste_nom || 'Non renseigné'} />}</FormField>
      <FormField label="Date de début" error={mutation.errors.date_debut}>{(a11y) => <input {...a11y} type="date" value={form.date_debut} onChange={change('date_debut')} required />}</FormField>
      <FormField label="Date de fin (facultative)" error={mutation.errors.date_fin}>{(a11y) => <input {...a11y} type="date" min={form.date_debut || undefined} value={form.date_fin} onChange={change('date_fin')} />}</FormField>
      <FormField label="Salaire mensuel de base (XOF)" error={mutation.errors.salaire_base}>{(a11y) => <input {...a11y} type="number" min="0" step="0.01" value={form.salaire_base} onChange={change('salaire_base')} required />}</FormField>
      <FormField label="Heures de travail par jour" error={mutation.errors.heures_journalieres}>{(a11y) => <input {...a11y} type="number" min="0.01" max="24" step="0.01" value={form.heures_journalieres} onChange={change('heures_journalieres')} required />}</FormField>
      <FormField label="Statut du contrat" error={mutation.errors.statut}>{(a11y) => <select {...a11y} value={form.statut} onChange={change('statut')}>{Object.entries(contractStatuses).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select>}</FormField>
      <FormField label="Types de contrat" error={mutation.errors.type}>{(a11y) => canChooseTypes
        ? <select {...a11y} multiple value={form.type} onChange={(event) => setForm((value) => ({ ...value, type: Array.from(event.target.selectedOptions, (option) => option.value) }))}>{types.map((type) => <option key={type.id} value={type.id}>{type.type}</option>)}</select>
        : <input {...a11y} readOnly value={contract?.types_libelles?.join(', ') || 'Aucun type renseigné'} />}</FormField>
    </fieldset>
    <p>Plusieurs types peuvent être sélectionnés. Une date de fin vide correspond à un contrat sans fin renseignée.</p>
    {canChoosePosition && !positionsLoading && !positionsError && !positions.length && <p>Ajoutez un poste avec « Gérer les postes », puis sélectionnez-le ici.</p>}
    {mutation.message && <p className="message-box error" role="alert">{mutation.message}</p>}
    <div className="form-footer"><button type="button" className="outline-button" disabled={mutation.saving} onClick={onClose}>Annuler la saisie</button><button type="submit" className="primary-button" disabled={mutation.saving || (canChoosePosition && (positionsLoading || Boolean(positionsError)))}>{mutation.saving ? 'Enregistrement…' : 'Enregistrer le contrat'}</button></div>
  </form>;
}
