import React, { useId } from 'react';

/** @param {{ label: string, error?: string | Array, children: Function }} props */
export default function FormField({ label, error, children }) {
  const id = useId();
  const errorId = `${id}-error`;
  return <div className="form-field">
    <label htmlFor={id}>{label}</label>
    {children({ id, 'aria-invalid': Boolean(error), 'aria-describedby': error ? errorId : undefined })}
    {error && <small className="field-error" id={errorId}>{Array.isArray(error) ? error.join(' ') : String(error)}</small>}
  </div>;
}
