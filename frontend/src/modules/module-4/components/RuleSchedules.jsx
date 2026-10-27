import React from 'react';
import FormField from '../../../shared/components/FormField.jsx';

/** @param {{ form: Object, setForm: Function, errors: Object }} props */
export default function RuleSchedules({ form, setForm, errors }) {
  const change = (key, index, field) => (event) => setForm((value) => ({
    ...value, [key]: value[key].map((row, rowIndex) => rowIndex === index ? { ...row, [field]: event.target.value } : row),
  }));
  const remove = (key, index) => setForm((value) => ({ ...value, [key]: value[key].filter((_, rowIndex) => rowIndex !== index) }));
  const add = (key, row) => setForm((value) => ({ ...value, [key]: [...value[key], row] }));
  return <>
    <h3>Tranches IUTS</h3>
    <p>Montants en XOF, taux en pourcentage. Les tranches commencent à zéro et se suivent sans écart. Laissez le plafond de la dernière tranche vide.</p>
    {errors.tranches_iuts && <p className="field-error" role="alert">{[].concat(errors.tranches_iuts).join(' ')}</p>}
    {form.tranches_iuts.map((row, index) => <div className="payroll-rule-row" key={index}>
      <FormField label={`Tranche ${index + 1} : minimum`}>{(a11y) => <input {...a11y} type="number" min="0" step="0.01" value={row.minimum} onChange={change('tranches_iuts', index, 'minimum')} required />}</FormField>
      <FormField label={`Tranche ${index + 1} : plafond`}>{(a11y) => <input {...a11y} type="number" min="0" step="0.01" value={row.maximum} onChange={change('tranches_iuts', index, 'maximum')} />}</FormField>
      <FormField label={`Tranche ${index + 1} : taux (%)`}>{(a11y) => <input {...a11y} type="number" min="0" max="100" step="0.0001" value={row.taux} onChange={change('tranches_iuts', index, 'taux')} required />}</FormField>
      <button type="button" className="outline-button" disabled={form.tranches_iuts.length === 1} onClick={() => remove('tranches_iuts', index)} aria-label={`Retirer la tranche ${index + 1}`}>Retirer</button>
    </div>)}
    <button type="button" className="outline-button" onClick={() => add('tranches_iuts', { minimum: form.tranches_iuts.at(-1)?.maximum || '', maximum: '', taux: '' })}>Ajouter une tranche</button>
    <h3>Réductions IUTS pour charges familiales</h3>
    <p>Ajoutez les réductions applicables. Sans ligne correspondante, le calcul n’applique aucune réduction familiale.</p>
    {errors.reductions_iuts_charges && <p className="field-error" role="alert">{[].concat(errors.reductions_iuts_charges).join(' ')}</p>}
    {form.reductions_iuts_charges.map((row, index) => <div className="payroll-rule-row" key={index}>
      <FormField label={`Réduction ${index + 1} : nombre de charges`}>{(a11y) => <input {...a11y} type="number" min="0" max="4" step="1" value={row.charges} onChange={change('reductions_iuts_charges', index, 'charges')} required />}</FormField>
      <FormField label={`Réduction ${index + 1} : taux (%)`}>{(a11y) => <input {...a11y} type="number" min="0" max="100" step="0.0001" value={row.taux} onChange={change('reductions_iuts_charges', index, 'taux')} required />}</FormField>
      <button type="button" className="outline-button" onClick={() => remove('reductions_iuts_charges', index)} aria-label={`Retirer la réduction ${index + 1}`}>Retirer</button>
    </div>)}
    <button type="button" className="outline-button" onClick={() => add('reductions_iuts_charges', { charges: '', taux: '' })}>Ajouter une réduction</button>
  </>;
}
