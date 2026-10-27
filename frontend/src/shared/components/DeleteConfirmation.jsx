import React, { useEffect, useId, useRef } from 'react';

/** @param {{ description: string, busy: boolean, onConfirm: Function, onCancel: Function }} props */
export default function DeleteConfirmation({ description, busy, onConfirm, onCancel }) {
  const dialogRef = useRef(null);
  const titleId = useId();
  const descriptionId = useId();

  useEffect(() => {
    const dialog = dialogRef.current;
    dialog.showModal();
    return () => dialog.close();
  }, []);

  return (
    <dialog
      ref={dialogRef}
      className="delete-confirmation"
      aria-labelledby={titleId}
      aria-describedby={descriptionId}
      aria-busy={busy}
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) onCancel();
      }}
    >
      <h2 id={titleId}>Confirmer la suppression</h2>
      <p id={descriptionId}>{description}</p>
      <div className="form-footer">
        <button type="button" className="outline-button" onClick={onCancel} disabled={busy} autoFocus>Annuler</button>
        <button type="button" className="danger-button" onClick={onConfirm} disabled={busy}>
          {busy ? 'Suppression…' : 'Supprimer définitivement'}
        </button>
      </div>
    </dialog>
  );
}
