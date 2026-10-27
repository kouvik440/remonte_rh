import React from 'react';

/** @param {{ people: Array, absent: boolean }} props */
function PeopleList({ people, absent }) {
  return (
    <section className="planning-people-group">
      <h4>{absent ? 'Absents — congés validés' : 'Présents prévus'} ({people.length})</h4>
      {people.length === 0 ? <p>Aucune personne dans cette catégorie.</p> : (
        <ul className="planning-people-list">
          {people.map((person) => (
            <li key={person.employe_id}>
              <strong>{person.employe_prenom} {person.employe_nom}</strong>
              <span>{person.departement_nom || 'Département non renseigné'}</span>
              {absent ? <ul>{person.absences.map((absence) => (
                <li key={absence.id}>
                  {absence.type_conge_libelle || 'Congé'}
                  {' — du '}{new Date(`${absence.date_debut}T12:00:00`).toLocaleDateString('fr-FR')}
                  {' au '}{new Date(`${absence.date_fin}T12:00:00`).toLocaleDateString('fr-FR')}
                </li>
              ))}</ul> : <span>Présence prévue · hors absence validée</span>}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

/** @param {{ people: Array, date: string }} props */
export default function PlanningRoster({ people, date }) {
  const absent = people.filter((person) => person.absences.length > 0);
  const present = people.filter((person) => person.absences.length === 0);
  return (
    <section className="planning-roster" aria-labelledby="planningRosterTitle">
      <h3 id="planningRosterTitle">
        Effectif du {new Date(`${date}T12:00:00`).toLocaleDateString('fr-FR', { dateStyle: 'full' })}
      </h3>
      <p role="status">{present.length} présent(s) prévu(s) · {absent.length} absent(s) · {people.length} personne(s)</p>
      {people.length === 0 && <p>Aucun événement pour ce jour et ces filtres. Les jours sans événement ne confirment pas une présence.</p>}
      <div className="planning-roster-columns">
        <PeopleList people={present} absent={false} />
        <PeopleList people={absent} absent />
      </div>
    </section>
  );
}
