import React, { useState } from 'react';
import FormField from '../../../shared/components/FormField.jsx';
import PayrollDialog from './PayrollDialog.jsx';
import PayrollContractPreview from './PayrollContractPreview.jsx';
import { actionLabels, employeeName, payrollPath, ruleLabel } from '../lib/payroll.js';

const endpoints = { calculate: 'calculer', validate: 'valider', cancel: 'annuler', generate: 'bulletin' };

/** @param {{ action: string, payroll: Object, rules: Array, rulesError: string, mutation: Object, onClose: Function, onSaved: Function }} props */
export default function PayrollAction({ action, payroll, rules, rulesError, mutation, onClose, onSaved }) {
  const [ruleId, setRuleId] = useState('');
  const [charges, setCharges] = useState('0');
  const [reason, setReason] = useState('');
  const confirm = async (event) => {
    event.preventDefault();
    const payload = action === 'calculate' ? { charges_familiales: Number(charges), ...(ruleId ? { regle_paie: Number(ruleId) } : {}) }
      : action === 'cancel' ? { motif: reason.trim() } : {};
    const path = `${payrollPath}${payroll.id}/${action === 'delete' ? '' : `${endpoints[action]}/`}`;
    if (await mutation.submit(path, action === 'delete' ? 'DELETE' : 'POST', payload)) onSaved();
  };
  return <PayrollDialog title={actionLabels[action]} busy={mutation.saving} onClose={onClose}>
    <p>{employeeName(payroll)} · {payroll.periode} · {payroll.libelle}</p>
    {action === 'delete' && <p>Ce brouillon sera supprimé définitivement.</p>}
    {action === 'validate' && <p>Confirmer la validation des montants calculés ? Le bulletin PDF sera généré et archivé automatiquement.</p>}
    <form onSubmit={confirm}>
      <fieldset className="leave-form-grid" disabled={mutation.saving}>
        {action === 'calculate' && <>
          <FormField label="Profil de règles" error={mutation.errors.regle_paie}>{(a11y) => <select {...a11y} value={ruleId} onChange={(event) => setRuleId(event.target.value)}>
            <option value="">Sélection automatique selon la période</option>
            {rules.filter((rule) => rule.actif && rule.valide).map((rule) => <option key={rule.id} value={rule.id}>{ruleLabel(rule)}</option>)}
          </select>}</FormField>
          <FormField label="Charges familiales (0 à 4)" error={mutation.errors.charges_familiales}>{(a11y) => <input {...a11y} type="number" min="0" max="4" step="1" value={charges} onChange={(event) => setCharges(event.target.value)} required />}</FormField>
        </>}
        {action === 'cancel' && <FormField label="Motif d’annulation" error={mutation.errors.motif}>{(a11y) => <textarea {...a11y} value={reason} onChange={(event) => setReason(event.target.value)} maxLength={500} required />}</FormField>}
      </fieldset>
      {action === 'calculate' && <><PayrollContractPreview employeeId={payroll.employe} period={payroll.periode} /><p>Le serveur vérifie le contrat et le profil couvrant la période. Les éléments variables non validés sont exclus du calcul.</p></>}
      {action === 'calculate' && !rules.some((rule) => rule.actif && rule.valide) && <p className="message-box">Créez et validez un profil dans « Règles de paie » avant de lancer le calcul.</p>}
      {action === 'calculate' && rulesError && <p className="message-box error" role="alert">Profils indisponibles : {rulesError}. Fermez puis actualisez la liste.</p>}
      {mutation.message && <p className="message-box error" role="alert">{mutation.message}</p>}
      <div className="form-footer">
        <button type="button" className="outline-button" onClick={onClose} disabled={mutation.saving} autoFocus>Fermer</button>
        <button type="submit" className={action === 'delete' || action === 'cancel' ? 'danger-button' : 'primary-button'} disabled={mutation.saving || (action === 'calculate' && Boolean(rulesError))}>
          {mutation.saving ? 'Traitement…' : actionLabels[action]}
        </button>
      </div>
    </form>
  </PayrollDialog>;
}
