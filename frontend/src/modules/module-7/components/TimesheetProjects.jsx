import React, { useState } from 'react';
import useApiResource from '../../../shared/hooks/useApiResource.js';
import { hasPermission } from '../../../shared/lib/api.js';
import useTimesheetMutation from '../hooks/useTimesheetMutation.js';
import TimesheetPanel from './TimesheetPanel.jsx';
import ProjectDetails from './ProjectDetails.jsx';
import ProjectNameForm from './ProjectNameForm.jsx';
import Field from './TimesheetField.jsx';
import ResourceState from './ResourceState.jsx';

export default function TimesheetProjects() {
  const data = useApiResource('/api/projets/');
  const mutation = useTimesheetMutation();
  const [selected, setSelected] = useState('');
  const [creating, setCreating] = useState(false);
  const project = data.report?.find((item) => String(item.id) === selected);
  return <TimesheetPanel title="Préparer les projets et prestations" description="Créez le projet, ajoutez ses tâches et affectez les employés avant leur saisie du temps."
    actions={<div className="timesheet-actions"><button className="outline-button" type="button" disabled={data.loading || mutation.busy} onClick={data.reload}>Actualiser les projets</button>
      {hasPermission('projet.create') && <button className="primary-button" type="button" disabled={mutation.busy} onClick={() => { mutation.reset(); setCreating(true); }}>Nouveau projet</button>}</div>}>
    <ResourceState data={data} label="des projets">{(items) => <>
      {!items.length ? <p role="status">Aucun projet enregistré.</p> : <Field label="Projet à préparer"><select value={selected} onChange={(event) => setSelected(event.target.value)}>
        <option value="">Choisir un projet</option>{items.map((item) => <option key={item.id} value={item.id}>{item.nom}{item.actif ? '' : ' (inactif)'}</option>)}
      </select></Field>}
      {project && <ProjectDetails key={project.id} project={project} />}
    </>}</ResourceState>
    {creating && <ProjectNameForm title="Nouveau projet" path="/api/projets/" mutation={mutation} onClose={() => setCreating(false)} onSaved={(result) => { setCreating(false); setSelected(String(result.id)); data.reload(); }} />}
  </TimesheetPanel>;
}
