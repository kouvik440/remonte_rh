import React, { useState } from 'react';
import ModalDialog from '../../../shared/components/ModalDialog.jsx';
import { currentMonday, sheetPath, sheetPayload, validateSheet, weekEnd } from '../lib/timesheets.js';
import Field from './TimesheetField.jsx';
import ResourceState from './ResourceState.jsx';

let lineId = 0;
const blankLine = (date) => ({ key: `draft-${++lineId}`, date, project: '', task: '', unit: 'heures', quantity: '', comment: '' });

export default function TimesheetEditor({ sheet, initialProject = '', projects, mutation, onClose, onSaved }) {
  const [week, setWeek] = useState(sheet?.semaine_debut || currentMonday());
  const [lines, setLines] = useState(() => sheet ? sheet.lignes.map((line) => ({ key: `saved-${line.id}`, date: line.date_travail,
    project: String(line.projet), task: String(line.tache), unit: 'heures', quantity: line.heures, comment: line.commentaire,
    projectName: line.projet_nom, taskName: line.tache_nom })) : [{ ...blankLine(currentMonday()), project: String(initialProject) }]);
  const [errors, setErrors] = useState({});
  function update(key, changes) {
    setLines((current) => current.map((line) => line.key === key ? { ...line, ...changes } : line));
  }
  function save(event) {
    event.preventDefault();
    const nextErrors = validateSheet(week, lines, projects.report || []);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;
    mutation.run(sheet ? `${sheetPath}${sheet.id}/` : sheetPath, sheet ? 'PUT' : 'POST', sheetPayload(week, lines), onSaved);
  }
  return <ModalDialog title={sheet ? `Modifier la semaine du ${week}` : 'Nouvelle feuille de temps'} busy={mutation.busy} onClose={onClose}>
    <p>Renseignez chaque date, projet et tâche. Une journée vaut l’horaire prévu au contrat pour la date choisie.</p>
    <button type="button" className="outline-button" disabled={mutation.busy || projects.loading} onClick={projects.reload}>Actualiser les projets et tâches</button>
    {sheet?.statut === 'VALIDEE' && <p className="message-box" role="status">Enregistrer cette modification remettra la feuille en brouillon. Ses heures sortiront des coûts projets jusqu’à une nouvelle validation.</p>}
    <ResourceState data={projects} label="des projets affectés">{(options) => <form onSubmit={save} noValidate aria-busy={mutation.busy}>
      {!options.length && <p className="message-box" role="status">Aucun projet actif ne vous est affecté. Demandez une affectation et une tâche à votre responsable.</p>}
      <Field label="Lundi de la semaine" error={errors.week}><input type="date" value={week} min="0001-01-01" max="9999-12-25" disabled={Boolean(sheet) || mutation.busy}
        onChange={(event) => { const next = event.target.value; setLines((current) => current.map((line) => line.date === week ? { ...line, date: next } : line)); setWeek(next); }} required /></Field>
      <div className="timesheet-editor-lines">
        {lines.map((line, index) => {
          const tasks = options.find((project) => String(project.id) === line.project)?.taches || [];
          const error = (field) => errors[`line-${index}-${field}`];
          return <fieldset className="timesheet-line-editor" key={line.key} disabled={mutation.busy}>
            <legend>Ligne {index + 1}</legend>
            <div className="timesheet-line-fields">
              <Field label="Date travaillée" error={error('date')}><input type="date" value={line.date} min={week} max={weekEnd(week)} required onChange={(event) => update(line.key, { date: event.target.value })} /></Field>
              <Field label="Projet" error={error('project')}><select value={line.project} required onChange={(event) => update(line.key, { project: event.target.value, task: '' })}>
                <option value="">Choisir un projet</option>
                {line.project && !options.some((item) => String(item.id) === line.project) && <option value={line.project} disabled>{line.projectName || 'Ancien projet'} (indisponible)</option>}
                {options.map((project) => <option value={project.id} key={project.id}>{project.nom}</option>)}
              </select></Field>
              <Field label="Tâche" error={error('task')}><select value={line.task} required onChange={(event) => update(line.key, { task: event.target.value })}>
                <option value="">Choisir une tâche</option>
                {line.task && !tasks.some((item) => String(item.id) === line.task) && <option value={line.task} disabled>{line.taskName || 'Ancienne tâche'} (indisponible)</option>}
                {tasks.map((task) => <option key={task.id} value={task.id}>{task.nom}</option>)}
              </select></Field>
              {line.project && !tasks.length && <p className="timesheet-note">Aucune tâche active dans ce projet. Demandez à votre responsable d’en ajouter une, puis actualisez la liste.</p>}
              <Field label="Unité"><select value={line.unit} onChange={(event) => update(line.key, { unit: event.target.value, quantity: '' })}>
                <option value="heures">Heures</option><option value="jours">Jours / fraction de jour</option>
              </select></Field>
              <Field label={line.unit === 'jours' ? 'Nombre de jours' : 'Nombre d’heures'} error={error('quantity')}><input inputMode="decimal" value={line.quantity} required
                placeholder={line.unit === 'jours' ? 'Ex. 0,5' : 'Ex. 3,5'} onChange={(event) => update(line.key, { quantity: event.target.value })} /></Field>
              <Field label="Commentaire"><input value={line.comment} onChange={(event) => update(line.key, { comment: event.target.value })} /></Field>
            </div>
            <button type="button" className="danger-button" onClick={() => setLines((current) => current.filter((item) => item.key !== line.key))}>Retirer la ligne {index + 1}</button>
          </fieldset>;
        })}
      </div>
      <button type="button" className="outline-button" disabled={mutation.busy || !options.length} onClick={() => setLines((current) => [...current, blankLine(week)])}>Ajouter une ligne</button>
      {!lines.length && <p className="timesheet-note">Ce brouillon est vide. Ajoutez une ligne avant de le soumettre.</p>}
      {Object.keys(errors).length > 0 && <p className="message-box error" role="alert">Corrigez les champs indiqués avant d’enregistrer.</p>}
      {mutation.error && <p className="message-box error" role="alert">{mutation.error}</p>}
      <div className="form-footer"><button type="button" className="outline-button" disabled={mutation.busy} onClick={onClose}>Annuler</button>
        <button type="submit" className="primary-button" disabled={mutation.busy}>{mutation.busy ? 'Enregistrement…' : 'Enregistrer le brouillon'}</button></div>
    </form>}</ResourceState>
  </ModalDialog>;
}
