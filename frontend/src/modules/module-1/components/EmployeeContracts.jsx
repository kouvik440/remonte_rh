import React, { useState } from 'react';
import ModalDialog from '../../../shared/components/ModalDialog.jsx';
import useApiMutation from '../../../shared/hooks/useApiMutation.js';
import { hasPermission } from '../../../shared/lib/api.js';
import useEmployeeContracts from '../hooks/useEmployeeContracts.js';
import ContractEditor, { contractStatuses } from './ContractEditor.jsx';
import ContractTypeManager from './ContractTypeManager.jsx';
import PositionManager from './PositionManager.jsx';

/** @param {{ employee: Object, onClose: Function }} props */
export default function EmployeeContracts({ employee, onClose }) {
  const readTypes = hasPermission('type_contrat.read');
  const readPositions = hasPermission('poste.read');
  const data = useEmployeeContracts(employee.id, readTypes, readPositions);
  const mutation = useApiMutation(data.load);
  const [editor, setEditor] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const [notice, setNotice] = useState('');
  const [typesOpen, setTypesOpen] = useState(false);
  const [positionsOpen, setPositionsOpen] = useState(false);
  const open = (contract) => { mutation.reset(); setNotice(''); setEditor({ contract }); };
  const remove = async () => {
    if (await mutation.submit(`/api/contrats/${deleting.id}/`, 'DELETE')) { setDeleting(null); setNotice('Contrat supprimé.'); }
  };
  return <ModalDialog title={`Contrats · ${employee.prenom} ${employee.nom}`} busy={mutation.saving} onClose={onClose}>
    <p>Matricule : {employee.matricule}. Le contrat fournit la base de salaire et les heures utilisées pour la paie et les feuilles de temps.</p>
    {readTypes && <button type="button" className="outline-button" disabled={mutation.saving} onClick={() => setTypesOpen(true)}>Gérer les types de contrat</button>}
    {readPositions && <button type="button" className="outline-button" disabled={mutation.saving} onClick={() => setPositionsOpen(true)}>Gérer les postes</button>}
    {positionsOpen && <PositionManager onClose={() => setPositionsOpen(false)} onChanged={data.load} />}
    {typesOpen && <ContractTypeManager onClose={() => setTypesOpen(false)} onChanged={data.load} />}
    {notice && <p className="message-box" role="status">{notice}</p>}
    {data.typesError && <p className="message-box error" role="alert">Types de contrat : {data.typesError}</p>}
    {data.positionsError && <p className="message-box error" role="alert">Postes : {data.positionsError}</p>}
    {editor ? <ContractEditor key={editor.contract?.id || 'new'} contract={editor.contract} employeeId={employee.id} types={data.types}
      positions={data.positions} canChoosePosition={readPositions} positionsLoading={data.loading} positionsError={data.positionsError}
      canChooseTypes={readTypes && !data.typesError} mutation={mutation} onClose={() => setEditor(null)}
      onSaved={() => { setEditor(null); setNotice('Contrat enregistré.'); }} /> : deleting ? null : <>
      <div className="form-footer"><button type="button" className="outline-button" onClick={data.load} disabled={data.loading || mutation.saving}>Actualiser</button>
        {hasPermission('contrat.create') && <button type="button" className="primary-button" onClick={() => open(null)} disabled={data.loading || mutation.saving || !readPositions || Boolean(data.positionsError)}>Nouveau contrat</button>}</div>
      {!readPositions && hasPermission('contrat.create') && <p>La consultation du catalogue des postes est nécessaire pour préparer un nouveau contrat.</p>}
      {data.loading ? <p role="status">Chargement des contrats…</p> : data.error ? <p className="message-box error" role="alert">{data.error}</p>
        : <ContractList contracts={data.contracts} busy={mutation.saving} onEdit={open} onDelete={(contract) => { mutation.reset(); setDeleting(contract); }} />}
    </>}
    {deleting && <section className="message-box" role="alert">
      <h3>Supprimer ce contrat ?</h3><p>Contrat du {deleting.date_debut}. Les calculs déjà enregistrés conservent leur historique.</p>
      {mutation.message && <p className="field-error">{mutation.message}</p>}
      <div className="form-footer"><button type="button" className="outline-button" onClick={() => setDeleting(null)} disabled={mutation.saving}>Conserver</button><button type="button" className="danger-button" onClick={remove} disabled={mutation.saving}>Confirmer la suppression</button></div>
    </section>}
    <div className="form-footer"><button type="button" className="outline-button" onClick={onClose} disabled={mutation.saving}>Fermer</button></div>
  </ModalDialog>;
}

/** @param {{ contracts: Array, busy: boolean, onEdit: Function, onDelete: Function }} props */
export function ContractList({ contracts, busy, onEdit, onDelete }) {
  if (!contracts.length) return <p>Aucun contrat enregistré pour cet employé.</p>;
  return <div className="contract-list">{contracts.map((contract) => <article className="leave-request-card payroll-card" key={contract.id}>
    <div className="leave-request-main"><h3>{contract.types_libelles?.join(', ') || 'Contrat'} · {contractStatuses[contract.statut] || contract.statut}</h3>
      <p>Du {contract.date_debut} au {contract.date_fin || 'Non renseigné'}</p>
      <p>Poste : {contract.poste_nom || 'Non renseigné'}</p>
      <p>Base mensuelle : {new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'XOF' }).format(Number(contract.salaire_base))} · {contract.heures_journalieres || 'Non renseigné'} h/jour</p>
    </div><div className="leave-request-actions">
      {hasPermission('contrat.update') && <button type="button" className="outline-button" onClick={() => onEdit(contract)} disabled={busy}>Modifier</button>}
      {hasPermission('contrat.delete') && <button type="button" className="danger-button" onClick={() => onDelete(contract)} disabled={busy}>Supprimer</button>}
    </div>
  </article>)}</div>;
}
