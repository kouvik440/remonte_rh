import React from 'react';
import ModalDialog from '../../../shared/components/ModalDialog.jsx';
import useApiResource from '../../../shared/hooks/useApiResource.js';

const categories = { POSTE: 'Poste', CONTRAT: 'Contrat', RESPONSABLE: 'Responsable hiérarchique' };
const operations = { INITIAL: 'État initial', CREATION: 'Création', MODIFICATION: 'Modification', SUPPRESSION: 'Suppression' };
const labels = { nom: 'Nom', description: 'Description', date_debut: 'Début', date_fin: 'Fin', salaire_base: 'Salaire de base (XOF)', heures_journalieres: 'Heures par jour', statut: 'Statut', types_contrat: 'Types de contrat' };
const statuses = { EN_COURS: 'En cours', CLOS: 'Clos', RESILIE: 'Résilié' };

function Snapshot({ value }) {
  if (!Object.keys(value).length) return <p>Non renseigné</p>;
  return <dl className="employee-history-values">{Object.entries(value).filter(([key]) => key !== 'id').map(([key, item]) => <div key={key}>
    <dt>{key === 'poste' ? 'Poste' : labels[key] || key}</dt><dd>{Array.isArray(item) ? item.map((entry) => entry.libelle).join(', ') || '—' : item && typeof item === 'object' ? item.nom || '—' : statuses[item] || item || '—'}</dd>
  </div>)}</dl>;
}

export default function EmployeeHistory({ employee, onClose }) {
  const data = useApiResource(`/api/employes/${employee.id}/historique/`);
  return <ModalDialog title={`Historique professionnel · ${employee.prenom} ${employee.nom}`} onClose={onClose}>
    <p>Les événements conservent les valeurs avant et après chaque changement. L’état initial correspond aux informations présentes lors de l’activation de l’historique.</p>
    <button className="outline-button" type="button" disabled={data.loading} onClick={data.reload}>Actualiser l’historique</button>
    {data.loading && <p role="status">Chargement de l’historique…</p>}
    {data.error && <p className="message-box error" role="alert">{data.error}</p>}
    {!data.loading && !data.error && (!(data.report || []).length ? <p>Aucun événement professionnel enregistré.</p> : <div className="employee-history-list">
      {data.report.map((event) => <article key={event.id} className="employee-history-event">
        <h3>{categories[event.categorie]} · {operations[event.operation]}</h3>
        <p>{new Intl.DateTimeFormat('fr-FR', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(event.date_evenement))} · {event.auteur_nom || 'Reprise des données / système'}</p>
        <div className="employee-history-columns"><section><h4>Avant</h4><Snapshot value={event.avant} /></section><section><h4>Après</h4><Snapshot value={event.apres} /></section></div>
      </article>)}
    </div>)}
    <div className="form-footer"><button className="outline-button" type="button" onClick={onClose}>Fermer</button></div>
  </ModalDialog>;
}
