import React, { useEffect, useId, useRef } from 'react';
import { X } from 'lucide-react';
import useBodyScrollLock from '../hooks/useBodyScrollLock.js';

/** @param {{ title: string, busy?: boolean, onClose: Function, children: React.ReactNode }} props */
export default function ModalDialog({ title, busy = false, onClose, children }) {
  const ref = useRef(null);
  const titleId = useId();
  useBodyScrollLock(true);
  useEffect(() => {
    const dialog = ref.current;
    dialog.showModal();
    return () => dialog.close();
  }, []);
  return <dialog ref={ref} className="leave-detail-dialog form-dialog" aria-labelledby={titleId} aria-busy={busy}
    onCancel={(event) => { event.preventDefault(); if (!busy) onClose(); }}>
    <div className="dialog-heading">
      <h2 id={titleId}>{title}</h2>
      <button type="button" className="icon-button dialog-close" aria-label="Fermer la fenêtre" disabled={busy} onClick={onClose}>
        <X size={20} aria-hidden="true" />
      </button>
    </div>
    {children}
  </dialog>;
}
