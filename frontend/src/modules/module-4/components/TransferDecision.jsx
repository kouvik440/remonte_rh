import React, { useState } from 'react';
import FormField from '../../../shared/components/FormField.jsx';
import PayrollDialog from './PayrollDialog.jsx';
import { employeeName, money, payrollPath } from '../lib/payroll.js';
import { reconcilablePayrolls, transferLabels, transfersPath } from '../lib/transfers.js';

/** @param {{ action: string, order: Object, payrolls: Array, mutation: Object, onClose: Function, onSaved: Function }} props */
export default function TransferDecision({ action, order, payrolls, mutation, onClose, onSaved }) {
  const [reason, setReason] = useState('');
  const candidates = reconcilablePayrolls(order, payrolls);
  const [payrollId, setPayrollId] = useState(String(candidates[0]?.id || ''));
  const selected = candidates.find((payroll) => String(payroll.id) === payrollId);
  const confirm = async (event) => {
    event.preventDefault();
    if (action === 'reconcile' && !selected) return;
    const path = action === 'reconcile' ? `${payrollPath}${selected.id}/marquer-payee/`
      : `${transfersPath}${order.id}/${action === 'delete' ? '' : `${action}/`}`;
    const payload = action === 'reconcile' ? { ordre_virement: order.id } : { motif: reason.trim() };
    if (await mutation.submit(path, action === 'delete' ? 'DELETE' : 'POST', action === 'delete' ? undefined : payload)) onSaved();
  };
  return <PayrollDialog title={transferLabels[action]} busy={mutation.saving} onClose={onClose}>
    <p>Ordre #{order.id} · {employeeName(order)} · {order.periode}</p>
    {action === 'delete' && <p>La suppression de cet ordre généré est définitive.</p>}
    {action === 'traiter' && <p>Confirmez l’enregistrement du traitement de cet ordre. L’auteur et la date seront conservés.</p>}
    <form onSubmit={confirm}>
      <fieldset className="leave-form-grid" disabled={mutation.saving}>
        {action === 'reconcile' ? <FormField label="Paie validée à associer" error={mutation.errors.ordre_virement}>{(a11y) => <select {...a11y} value={payrollId} onChange={(event) => setPayrollId(event.target.value)} required>
          <option value="">Choisir la paie</option>{candidates.map((payroll) => <option key={payroll.id} value={payroll.id}>{payroll.libelle} · {money(payroll.salaire_net, payroll.devise)}</option>)}
        </select>}</FormField> : action !== 'delete' && <FormField label={action === 'traiter' ? 'Commentaire (facultatif)' : 'Motif de la décision'} error={mutation.errors.motif}>{(a11y) => <textarea {...a11y} value={reason} onChange={(event) => setReason(event.target.value)} maxLength={500} required={action !== 'traiter'} />}</FormField>}
      </fieldset>
      {action === 'reconcile' && <p>La paie passera au statut « Payée » avec la date de traitement de cet ordre. Cette action enregistre le suivi interne du paiement.</p>}
      {mutation.message && <p className="message-box error" role="alert">{mutation.message}</p>}
      <div className="form-footer"><button type="button" className="outline-button" disabled={mutation.saving} onClick={onClose} autoFocus>Fermer</button><button type="submit" className={['delete', 'rejeter', 'annuler'].includes(action) ? 'danger-button' : 'primary-button'} disabled={mutation.saving || (action === 'reconcile' && !selected)}>{mutation.saving ? 'Traitement…' : 'Confirmer'}</button></div>
    </form>
  </PayrollDialog>;
}
