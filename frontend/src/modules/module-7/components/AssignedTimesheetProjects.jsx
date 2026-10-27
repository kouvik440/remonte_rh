import React from 'react';
import TimesheetPanel from './TimesheetPanel.jsx';
import ResourceState from './ResourceState.jsx';

export default function AssignedTimesheetProjects({ projects, onStart, busy }) {
  return <TimesheetPanel title="Mes projets et tâches affectés" description="Retrouvez les tâches à renseigner. Les tâches présentes dans vos feuilles validées sont retirées de cette liste."
    actions={<button type="button" className="outline-button" disabled={projects.loading} onClick={projects.reload}>Actualiser mes affectations</button>}>
    <ResourceState data={projects} label="de mes affectations">{(items) => !items.length
      ? <p role="status">Aucune tâche en attente de saisie. Retrouvez vos feuilles validées dans « Mes feuilles de temps ».</p>
      : <div className="timesheet-list">{items.map((project) => <article className="timesheet-item" key={project.id}>
        <h3>{project.nom}</h3>
        {project.taches.length ? <ul className="timesheet-simple-list">{project.taches.map((task) => <li key={task.id}>{task.nom}</li>)}</ul>
          : <p>Aucune tâche active. Votre responsable doit en ajouter une pour permettre la saisie.</p>}
        <button type="button" className="primary-button" disabled={busy || !project.taches.length} onClick={() => onStart(project.id)}>Saisir mon temps sur {project.nom}</button>
      </article>)}</div>}</ResourceState>
  </TimesheetPanel>;
}
