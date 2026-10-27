import React, { useEffect, useId, useRef } from 'react';

const actionLabels = { valider: 'Valider', refuser: 'Refuser', supprimer: 'Supprimer' };

/** @param {{ action: string, request: Object, busy: boolean, onCancel: Function, onConfirm: Function }} props */
export default function LeaveActionConfirmation({ action, request, busy, onCancel, onConfirm }) {
  const dialogRef = useRef(null);
  const titleId = useId();
  const descriptionId = useId();
  useEffect(() => {
    const dialog = dialogRef.current;
    dialog.showModal();
    return () => dialog.close();
  }, []);
  return (
    <dialog ref={dialogRef} className="leave-detail-dialog" aria-labelledby={titleId}
      aria-describedby={descriptionId} aria-busy={busy}
      onCancel={(event) => { event.preventDefault(); if (!busy) onCancel(); }}>
      <h2 id={titleId}>{actionLabels[action]} la demande #{request.id} ?</h2>
      <p id={descriptionId}>
        {request.type_conge_libelle} · du {request.date_debut} au {request.date_fin}.
        {action === 'supprimer' && ' Cette suppression est définitive.'}
      </p>
      <div className="form-footer">
        <button type="button" className="outline-button" disabled={busy} onClick={onCancel} autoFocus>Annuler</button>
        <button type="button" className="primary-button" disabled={busy} onClick={onConfirm}>
          {busy ? 'Enregistrement…' : `Confirmer : ${actionLabels[action]}`}
        </button>
      </div>
    </dialog>
  );
}
