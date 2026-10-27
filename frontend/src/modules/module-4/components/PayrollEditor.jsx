import React, { useState } from 'react';
import FormField from '../../../shared/components/FormField.jsx';
import PayrollDialog from './PayrollDialog.jsx';
import PayrollContractPreview from './PayrollContractPreview.jsx';
import { currentPeriod, payrollPath } from '../lib/payroll.js';

/** @param {{ payroll: Object | null, employees: Array, canChooseEmployee: boolean, mutation: Object, onClose: Function, onSaved: Function }} props */
export default function PayrollEditor({ payroll, employees, canChooseEmployee, mutation, onClose, onSaved }) {
  const [form, setForm] = useState({ employe: payroll?.employe || '', periode: payroll?.periode || currentPeriod(), libelle: payroll?.libelle || '' });
  const change = (key) => (event) => setForm((value) => ({ ...value, [key]: event.target.value }));
  const save = async (event) => {
    event.preventDefault();
    const payload = { ...form, employe: Number(form.employe) };
    const success = await mutation.submit(payroll ? `${payrollPath}${payroll.id}/` : payrollPath, payroll ? 'PUT' : 'POST', payload);
    if (success) onSaved();
  };
  return <PayrollDialog title={payroll ? 'Modifier le brouillon' : 'Nouvelle paie'} busy={mutation.saving} onClose={onClose}>
    <p>Les montants sont calculés à partir du contrat, des absences et des éléments variables validés.</p>
    <form onSubmit={save}>
      <fieldset className="leave-form-grid" disabled={mutation.saving}>
        <FormField label="Employé" error={mutation.errors.employe}>{(a11y) => canChooseEmployee
          ? <select {...a11y} value={form.employe} onChange={change('employe')} required>
            <option value="">Choisir un employé</option>
            {employees.map((employee) => <option key={employee.id} value={employee.id}>{employee.prenom} {employee.nom} · {employee.matricule}</option>)}
          </select>
          : <input {...a11y} value={`${payroll?.employe_prenom || ''} ${payroll?.employe_nom || ''}`.trim() || `Employé #${form.employe}`} readOnly />}</FormField>
        <FormField label="Période" error={mutation.errors.periode}>{(a11y) => <input {...a11y} type="month" value={form.periode} onChange={change('periode')} required />}</FormField>
        <FormField label="Libellé" error={mutation.errors.libelle}>{(a11y) => <input {...a11y} value={form.libelle} onChange={change('libelle')} maxLength={150} required />}</FormField>
      </fieldset>
      <PayrollContractPreview employeeId={form.employe} period={form.periode} />
      {mutation.message && <p className="message-box error" role="alert">{mutation.message}</p>}
      <div className="form-footer">
        <button className="outline-button" type="button" onClick={onClose} disabled={mutation.saving}>Fermer</button>
        <button className="primary-button" type="submit" disabled={mutation.saving}>{mutation.saving ? 'Enregistrement…' : 'Enregistrer le brouillon'}</button>
      </div>
    </form>
  </PayrollDialog>;
}
