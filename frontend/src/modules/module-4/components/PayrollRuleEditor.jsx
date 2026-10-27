import React, { useState } from 'react';
import FormField from '../../../shared/components/FormField.jsx';
import PayrollDialog from './PayrollDialog.jsx';
import RuleSchedules from './RuleSchedules.jsx';
import { rateFields, ruleForm, rulePayload, rulesPath } from '../lib/rules.js';

const identityFields = [
  ['code', 'Code du profil', 'text', 50], ['nom', 'Nom du profil', 'text', 150],
  ['date_debut', 'Date de début d’effet', 'date'], ['date_fin', 'Date de fin d’effet (facultative)', 'date'],
  ['source_reference', 'Référence des règles appliquées', 'text', 500],
];

/** @param {{ rule: Object | null, mutation: Object, onClose: Function, onSaved: Function }} props */
export default function PayrollRuleEditor({ rule, mutation, onClose, onSaved }) {
  const [form, setForm] = useState(() => ruleForm(rule));
  const change = (key) => (event) => setForm((value) => ({ ...value, [key]: event.target.value }));
  const save = async (event) => {
    event.preventDefault();
    if (await mutation.submit(rule?.id ? `${rulesPath}${rule.id}/` : rulesPath, rule?.id ? 'PUT' : 'POST', rulePayload(form))) onSaved();
  };
  return <PayrollDialog title={rule?.id ? 'Modifier les règles de paie' : 'Nouvelles règles de paie'} busy={mutation.saving} onClose={onClose}>
    <p>Profil Burkina Faso · XOF · semaine du lundi au vendredi. Renseignez les paramètres de votre organisation et leur référence. Tous les taux sont saisis en pourcentage.</p>
    <form onSubmit={save}>
      <fieldset className="payroll-rule-fields" disabled={mutation.saving}>
        <div className="form-grid">
          {identityFields.map(([key, label, type, maxLength]) => <FormField key={key} label={label} error={mutation.errors[key]}>{(a11y) => <input {...a11y} type={type} value={form[key]} onChange={change(key)} maxLength={maxLength} required={key !== 'date_fin'} />}</FormField>)}
          <FormField label="Heures mensuelles" error={mutation.errors.heures_mensuelles}>{(a11y) => <input {...a11y} type="number" min="0.01" max="99999.99" step="0.01" value={form.heures_mensuelles} onChange={change('heures_mensuelles')} required />}</FormField>
          <FormField label="Plafond CNSS (XOF)" error={mutation.errors.plafond_cnss}>{(a11y) => <input {...a11y} type="number" min="0.01" step="0.01" value={form.plafond_cnss} onChange={change('plafond_cnss')} required />}</FormField>
          {rateFields.map(([key, label]) => <FormField key={key} label={label} error={mutation.errors[key]}>{(a11y) => <input {...a11y} type="number" min="0" max="100" step="0.0001" value={form[key]} onChange={change(key)} required />}</FormField>)}
          <FormField label="Décimales des montants" error={mutation.errors.decimales_montant}>{(a11y) => <select {...a11y} value={form.decimales_montant} onChange={change('decimales_montant')}><option value="0">0</option><option value="1">1</option><option value="2">2</option></select>}</FormField>
          <label className="role-checkbox"><input type="checkbox" checked={form.actif} onChange={(event) => setForm((value) => ({ ...value, actif: event.target.checked }))} />Profil actif</label>
        </div>
        <RuleSchedules form={form} setForm={setForm} errors={mutation.errors} />
      </fieldset>
      {mutation.message && <p className="message-box error" role="alert">{mutation.message}</p>}
      <p>Après enregistrement, validez le profil pour l’utiliser dans un calcul. La validation fige ses paramètres.</p>
      <div className="form-footer"><button type="button" className="outline-button" disabled={mutation.saving} onClick={onClose}>Fermer</button><button type="submit" className="primary-button" disabled={mutation.saving}>{mutation.saving ? 'Enregistrement…' : 'Enregistrer les règles'}</button></div>
    </form>
  </PayrollDialog>;
}
