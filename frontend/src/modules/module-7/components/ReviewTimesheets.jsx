import React, { useState } from 'react';
import ModalDialog from '../../../shared/components/ModalDialog.jsx';
import useApiResource from '../../../shared/hooks/useApiResource.js';
import useTimesheetMutation from '../hooks/useTimesheetMutation.js';
import { sheetPath } from '../lib/timesheets.js';
import TimesheetPanel from './TimesheetPanel.jsx';
import TimesheetLines from './TimesheetLines.jsx';
import Field from './TimesheetField.jsx';
import ResourceState from './ResourceState.jsx';

export default function ReviewTimesheets() {
  const data = useApiResource(`${sheetPath}a-valider/`);
  const mutation = useTimesheetMutation();
  const [action, setAction] = useState(null);
  const [reason, setReason] = useState('');
  const [reasonError, setReasonError] = useState('');
  const [notice, setNotice] = useState('');
  function begin(kind, sheet) { mutation.reset(); setReason(''); setReasonError(''); setNotice(''); setAction({ kind, sheet }); }
  function decide(event) {
    event.preventDefault();
    if (action.kind === 'refuser' && !reason.trim()) { setReasonError('Expliquez la correction attendue.'); return; }
    setReasonError('');
    mutation.run(`${sheetPath}${action.sheet.id}/${action.kind}/`, 'POST', action.kind === 'refuser' ? { motif: reason.trim() } : undefined,
      () => { setNotice(action.kind === 'valider' ? 'Feuille validée. Ses heures alimentent maintenant les coûts projets.' : 'Feuille retournée en brouillon avec le motif de correction.'); setAction(null); data.reload(); });
  }
  return <TimesheetPanel title="Feuilles à valider" description="Consultez les lignes avant de valider ou de demander une correction. La file suit la permission de validation, tous projets confondus."
    actions={<button className="outline-button" type="button" disabled={data.loading || mutation.busy} onClick={data.reload}>Actualiser la file</button>}>
    {notice && <p className="message-box success" role="status">{notice}</p>}
    <ResourceState data={data} label="des feuilles soumises">{(sheets) => !sheets.length ? <p role="status">Aucune feuille en attente de validation.</p> : <div className="timesheet-list">
      {sheets.map((sheet) => <article className="timesheet-item" key={sheet.id}>
        <h3>{sheet.employe_prenom} {sheet.employe_nom} · {sheet.employe_matricule}</h3>
        <p className="timesheet-note">Semaine du {sheet.semaine_debut}</p>
        <TimesheetLines sheet={sheet} />
        <div className="timesheet-actions"><button className="primary-button" type="button" disabled={mutation.busy} onClick={() => begin('valider', sheet)}>Valider la feuille de {sheet.employe_prenom}</button>
          <button className="outline-button" type="button" disabled={mutation.busy} onClick={() => begin('refuser', sheet)}>Demander une correction à {sheet.employe_prenom}</button></div>
      </article>)}
    </div>}</ResourceState>
    {action && <ModalDialog title={action.kind === 'valider' ? 'Valider la feuille de temps' : 'Demander une correction'} busy={mutation.busy} onClose={() => setAction(null)}>
      <p>{action.sheet.employe_prenom} {action.sheet.employe_nom} · semaine du {action.sheet.semaine_debut} · {action.sheet.total_heures} h.</p>
      <form onSubmit={decide} noValidate>
        {action.kind === 'refuser' ? <Field label="Motif de correction" error={reasonError}><textarea value={reason} maxLength={2000} required disabled={mutation.busy} onChange={(event) => setReason(event.target.value)} /></Field>
          : <p>Confirmer ces heures pour le calcul des coûts projets ?</p>}
        {mutation.error && <p className="message-box error" role="alert">{mutation.error}</p>}
        <div className="form-footer"><button className="outline-button" type="button" disabled={mutation.busy} onClick={() => setAction(null)}>Annuler</button>
          <button className="primary-button" type="submit" disabled={mutation.busy}>{action.kind === 'valider' ? 'Confirmer la validation' : 'Retourner pour correction'}</button></div>
      </form>
    </ModalDialog>}
  </TimesheetPanel>;
}
