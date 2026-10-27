import React, { useId } from 'react';

export default function TimesheetField({ label, error, children }) {
  const id = useId();
  return <div className="form-field">
    <label htmlFor={id}>{label}</label>
    {React.cloneElement(children, { id, 'aria-invalid': Boolean(error), 'aria-describedby': error ? `${id}-error` : undefined })}
    {error && <small className="field-error" id={`${id}-error`}>{error}</small>}
  </div>;
}
