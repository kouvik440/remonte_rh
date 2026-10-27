import React, { useId } from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../shared/components/ui/select.jsx';

/** @param {{ label: string, value: string, options: Array, onChange: Function, disabled?: boolean }} props */
export default function MassSelect({ label, value, options, onChange, disabled = false }) {
  const id = useId();
  return <div className="form-field">
    <label htmlFor={id}>{label}</label>
    <Select value={value} onValueChange={onChange} disabled={disabled}>
      <SelectTrigger id={id} className="mass-select-trigger"><SelectValue /></SelectTrigger>
      <SelectContent position="popper" align="start" className="mass-select-popup">
        {options.map((option) => <SelectItem key={option.value} value={option.value}>{option.label}</SelectItem>)}
      </SelectContent>
    </Select>
  </div>;
}
