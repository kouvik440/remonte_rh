import React, { useState } from 'react';
import ModalDialog from '../../../shared/components/ModalDialog.jsx';
import useApiResource from '../../../shared/hooks/useApiResource.js';
import useTimesheetMutation from '../hooks/useTimesheetMutation.js';
import { parseDate, sheetPath, statusLabels } from '../lib/timesheets.js';
import TimesheetPanel from './TimesheetPanel.jsx';
import TimesheetLines from './TimesheetLines.jsx';
import TimesheetEditor from './TimesheetEditor.jsx';
import Field from './TimesheetField.jsx';
import ResourceState from './ResourceState.jsx';
import AssignedTimesheetProjects from './AssignedTimesheetProjects.jsx';

export default function MyTimesheets() {
  const [date, setDate] = useState('');
  const [appliedDate, setAppliedDate] = useState('');
  const [dateError, setDateError] = useState('');
  const data = useApiResource(`${sheetPath}${appliedDate ? `?date_travail=${appliedDate}` : ''}`);
  const projects = useApiResource(`${sheetPath}projets/`, true, { refreshOnFocus: true });
  const assignments = useApiResource(`${sheetPath}projets/?a_saisir=true`, true, { refreshOnFocus: true });
  const mutation = useTimesheetMutation();
  const [editor, setEditor] = useState(null);
  const [action, setAction] = useState(null);
  const [notice, setNotice] = useState('');
  function open(sheet, project = '') { mutation.reset(); setNotice(''); projects.reload(); setEditor({ sheet, project }); }
  function begin(kind, sheet) { mutation.reset(); setNotice(''); setAction({ kind, sheet }); }
  function changed(text) { setEditor(null); setAction(null); setNotice(text); data.reload(); assignments.reload(); }
  function confirm() {
    if (!action) return;
    const deleting = action.kind === 'delete';
    mutation.run(`${sheetPath}${action.sheet.id}/${deleting ? '' : 'soumettre/'}`, deleting ? 'DELETE' : 'POST', undefined,
      () => changed(deleting ? 'Brouillon supprimé.' : 'Feuille soumise au manager. Elle est verrouillée jusqu’à sa décision.'));
  }
  return <>
    <AssignedTimesheetProjects projects={assignments} busy={mutation.busy} onStart={(project) => open(null, project)} />
    <TimesheetPanel title="Mes feuilles de temps" description="Une feuille par semaine. Enregistrez votre brouillon, puis soumettez-le à votre responsable."
      actions={<button className="primary-button" type="button" disabled={mutation.busy} onClick={() => open(null)}>Nouvelle feuille</button>}>
      <form className="timesheet-filter" noValidate onSubmit={(event) => { event.preventDefault();
        if (date && !parseDate(date)) { setDateError('Choisissez une date valide.'); return; }
        setDateError(''); if (date === appliedDate) data.reload(); else setAppliedDate(date);
      }}>
        <Field label="Feuilles contenant une date" error={dateError}><input type="date" value={date} onChange={(event) => setDate(event.target.value)} /></Field>
        <button type="submit" className="outline-button" disabled={data.loading || mutation.busy}>Filtrer</button>
        <button type="button" className="outline-button" disabled={data.loading || mutation.busy} onClick={() => { setDate(''); setDateError(''); setAppliedDate(''); data.reload(); projects.reload(); }}>Toutes les semaines / Actualiser</button>
      </form>
      {notice && <p className="message-box success" role="status">{notice}</p>}
      <ResourceState data={data} label="de mes feuilles">{(sheets) => !sheets.length ? <p role="status">Aucune feuille pour ce périmètre.</p> : <div className="timesheet-list">
        {sheets.map((sheet) => <article className="timesheet-item" key={sheet.id}>
          <div className="timesheet-item-header"><h3>Semaine du {sheet.semaine_debut}</h3><span className={`timesheet-status status-${sheet.statut.toLowerCase()}`}>{statusLabels[sheet.statut]}</span></div>
          <details><summary>Voir les lignes · {sheet.total_heures} h · {sheet.jours_saisis} date(s)</summary><TimesheetLines sheet={sheet} /></details>
          <div className="timesheet-actions">
            {sheet.statut !== 'SOUMISE' && <button type="button" className="outline-button" disabled={mutation.busy} onClick={() => open(sheet)}>Modifier la semaine du {sheet.semaine_debut}</button>}
            {sheet.statut === 'BROUILLON' && <>
              <button type="button" className="primary-button" disabled={mutation.busy || !sheet.lignes.length} onClick={() => begin('submit', sheet)}>Soumettre la semaine du {sheet.semaine_debut}</button>
              <button type="button" className="danger-button" disabled={mutation.busy} onClick={() => begin('delete', sheet)}>Supprimer le brouillon du {sheet.semaine_debut}</button>
            </>}
            {sheet.statut === 'SOUMISE' && <p className="timesheet-note">En attente de décision. La modification et la suppression sont verrouillées.</p>}
          </div>
          {sheet.motif_refus && <p className="message-box">À corriger : {sheet.motif_refus}</p>}
        </article>)}
      </div>}</ResourceState>
    </TimesheetPanel>
    {editor && <TimesheetEditor sheet={editor.sheet} initialProject={editor.project} projects={projects} mutation={mutation} onClose={() => setEditor(null)} onSaved={() => changed('Brouillon enregistré. Vous pouvez maintenant le soumettre.')} />}
    {action && <ModalDialog title={action.kind === 'delete' ? 'Supprimer le brouillon' : 'Soumettre la feuille de temps'} busy={mutation.busy} onClose={() => setAction(null)}>
      <p>Semaine du {action.sheet.semaine_debut} · {action.sheet.total_heures} h.</p>
      <p>{action.kind === 'delete' ? 'Le brouillon et ses lignes seront supprimés.' : 'La feuille sera verrouillée jusqu’à la décision du manager. Seules les heures validées contribueront aux coûts projets.'}</p>
      {mutation.error && <p className="message-box error" role="alert">{mutation.error}</p>}
      <div className="form-footer"><button className="outline-button" type="button" disabled={mutation.busy} onClick={() => setAction(null)}>Annuler</button>
        <button className={action.kind === 'delete' ? 'danger-button' : 'primary-button'} type="button" disabled={mutation.busy} onClick={confirm}>{action.kind === 'delete' ? 'Confirmer la suppression' : 'Confirmer la soumission'}</button></div>
    </ModalDialog>}
  </>;
}
