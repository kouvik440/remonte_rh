import React, { useState } from 'react';
import FormField from '../../../shared/components/FormField.jsx';
import PayrollDialog from './PayrollDialog.jsx';
import { employeeName, money } from '../lib/payroll.js';
import { eligiblePayrolls, matchesPayroll, transfersPath } from '../lib/transfers.js';

/** @param {{ order: Object | null, payrolls: Array, orders: Array, mutation: Object, onClose: Function, onSaved: Function }} props */
export default function TransferEditor({ order, payrolls, orders, mutation, onClose, onSaved }) {
  const candidates = eligiblePayrolls(payrolls, orders, order);
  const [payrollId, setPayrollId] = useState(() => String(candidates.find((payroll) => order && matchesPayroll(order, payroll))?.id || ''));
  const selected = candidates.find((payroll) => String(payroll.id) === payrollId);
  const save = async (event) => {
    event.preventDefault();
    if (!selected) return;
    const payload = { employe: selected.employe, periode: selected.periode };
    if (order) payload.date_generation = order.date_generation;
    if (await mutation.submit(order ? `${transfersPath}${order.id}/` : transfersPath, order ? 'PUT' : 'POST', payload)) onSaved();
  };
  return <PayrollDialog title={order ? 'Modifier l’ordre de virement' : 'Nouvel ordre de virement'} busy={mutation.saving} onClose={onClose}>
    <p>Choisissez une paie validée sans ordre généré ou traité pour le même employé et la même période.</p>
    <form onSubmit={save}>
      <fieldset className="leave-form-grid" disabled={mutation.saving}>
        <FormField label="Paie à régler" error={mutation.errors.periode || mutation.errors.employe}>{(a11y) => <select {...a11y} value={payrollId} onChange={(event) => setPayrollId(event.target.value)} required><option value="">Choisir une paie validée</option>
          {candidates.map((payroll) => <option key={payroll.id} value={payroll.id}>{employeeName(payroll)} · {payroll.periode} · {money(payroll.salaire_net, payroll.devise)}</option>)}
        </select>}</FormField>
      </fieldset>
      {!candidates.length && <p className="message-box">Aucune paie éligible. Validez une paie ou consultez l’ordre déjà enregistré pour cette période.</p>}
      {selected && <p>Montant net de la paie : {money(selected.salaire_net, selected.devise)}. La date de génération est attribuée par le serveur.</p>}
      {mutation.message && <p className="message-box error" role="alert">{mutation.message}</p>}
      <div className="form-footer"><button type="button" className="outline-button" onClick={onClose} disabled={mutation.saving}>Fermer</button><button type="submit" className="primary-button" disabled={mutation.saving || !selected}>{mutation.saving ? 'Enregistrement…' : 'Enregistrer l’ordre'}</button></div>
    </form>
  </PayrollDialog>;
}
