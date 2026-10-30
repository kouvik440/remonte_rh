import React, { useState } from 'react';
import '../styles/projectManagement.css';
import useApiResource from '../../../shared/hooks/useApiResource.js';
import { hasPermission } from '../../../shared/lib/api.js';
import ProjectTable from './ProjectTable.jsx';
import useTimesheetMutation from '../hooks/useTimesheetMutation.js';
import TimesheetPanel from './TimesheetPanel.jsx';
import ProjectDetails from './ProjectDetails.jsx';
import ProjectNameForm from './ProjectNameForm.jsx';
import Field from './TimesheetField.jsx';
import ResourceState from './ResourceState.jsx';
import { matchesSearch } from '../lib/projectAssignments.js';

export default function TimesheetProjects() {
  const data = useApiResource('/api/projets/');
  const mutation = useTimesheetMutation();
  const [selected, setSelected] = useState('');
  const [search, setSearch] = useState('');
  const [creating, setCreating] = useState(false);
  const project = data.report?.find((item) => String(item.id) === selected);
  return <TimesheetPanel title="Préparer les projets et prestations" description="Créez les tâches et choisissez leurs employés en une seule opération."
    actions={<div className="timesheet-actions"><button className="outline-button" type="button" disabled={data.loading || mutation.busy} onClick={data.reload}>Actualiser</button>
      {hasPermission('projet.create') && <button className="primary-button" type="button" disabled={mutation.busy} onClick={() => { mutation.reset(); setCreating(true); }}>Nouveau projet</button>}</div>}>
    <ResourceState data={data} label="des projets">{(items) => {
      const filtered = items.filter((item) => matchesSearch(`${item.nom} ${item.description || ''}`, search));
      return <><div className="project-table-toolbar"><Field label="Rechercher un projet"><input type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Nom du projet" /></Field>
        <p role="status">{filtered.length} projet{filtered.length > 1 ? 's' : ''}{search && ` sur ${items.length}`}</p></div>
        {!items.length ? <p role="status">Aucun projet enregistré. Créez un projet pour ajouter ses tâches.</p>
          : !filtered.length ? <p role="status">Aucun projet ne correspond à votre recherche.</p>
          : <ProjectTable projects={filtered} selected={selected} onSelect={setSelected} />}
        <div id="selected-project-details">{project && <ProjectDetails key={project.id} project={project} />}</div>
      </>;
    }}</ResourceState>
    {creating && <ProjectNameForm title="Nouveau projet" path="/api/projets/" mutation={mutation} onClose={() => setCreating(false)} onSaved={(result) => { setCreating(false); setSearch(''); setSelected(String(result.id)); data.reload(); }} />}
  </TimesheetPanel>;
}
