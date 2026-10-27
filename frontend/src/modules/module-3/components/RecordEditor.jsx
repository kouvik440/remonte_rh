import React from 'react';
import FormField from '../../../shared/components/FormField.jsx';

function FieldInput({ field, value, onChange, accessibility }) {
  const props = { ...accessibility, required: field.required, value, onChange: (event) => onChange(event.target.value) };
  if (field.type === 'select') return <select {...props}>
    <option value="">Choisir…</option>{field.options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
  </select>;
  if (field.type === 'textarea') return <textarea {...props} rows="3" />;
  return <input {...props} type={field.type || 'text'} maxLength={field.maxLength} autoComplete="off" />;
}

/** @param {{ fields: Array, form: Object, setForm: Function, mutation: Object, onSave: Function, onCancel: Function }} props */
export default function RecordEditor({ fields, form, setForm, mutation, onSave, onCancel }) {
  const update = (name, value) => setForm((previous) => ({ ...previous, [name]: value }));
  return <form className="module-three-editor" onSubmit={onSave} aria-busy={mutation.saving}>
    <fieldset className="leave-form-grid" disabled={mutation.saving}>
      <legend>Informations à enregistrer</legend>
      {fields.map((field) => field.type === 'checkbox' ? (
        <label key={field.name}><input type="checkbox" checked={Boolean(form[field.name])} onChange={(event) => update(field.name, event.target.checked)} /> {field.label}</label>
      ) : field.type === 'multiple' ? (
        <fieldset className="module-three-people" key={field.name}>
          <legend>{field.label}</legend>
          {field.options.map((option) => <label key={option.value}>
            <input type="checkbox" checked={form[field.name].map(String).includes(String(option.value))} onChange={(event) => {
              update(field.name, event.target.checked ? [...form[field.name], option.value] : form[field.name].filter((id) => String(id) !== String(option.value)));
            }} /> {option.label}
          </label>)}
          {mutation.errors[field.name] && <p className="field-error" role="alert">{String(mutation.errors[field.name])}</p>}
        </fieldset>
      ) : <FormField key={field.name} label={field.label} error={mutation.errors[field.name]}>
        {(accessibility) => <FieldInput field={field} value={form[field.name]} accessibility={accessibility} onChange={(value) => update(field.name, value)} />}
      </FormField>)}
    </fieldset>
    <div className="form-footer">
      <button type="button" className="outline-button" disabled={mutation.saving} onClick={onCancel}>Annuler</button>
      <button type="submit" className="primary-button" disabled={mutation.saving}>{mutation.saving ? 'Enregistrement…' : 'Enregistrer'}</button>
    </div>
  </form>;
}
