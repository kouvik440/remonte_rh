import { dateKey } from './calendar.js';

export function indexPlanningDays(events, start, end) {
  const byDay = {};
  for (const event of events) {
    let current = event.date_debut < start ? start : event.date_debut;
    const last = event.date_fin > end ? end : event.date_fin;
    while (current <= last) {
      (byDay[current] ||= []).push(event);
      const next = new Date(`${current}T12:00:00`);
      next.setDate(next.getDate() + 1);
      current = dateKey(next);
    }
  }
  return byDay;
}

// Plusieurs événements ou rôles ne doivent pas multiplier les effectifs d'une personne.
export function groupPlanningPeople(events) {
  const people = new Map();
  for (const event of events) {
    const key = String(event.employe_id);
    const person = people.get(key) || { ...event, absences: [] };
    if (event.type_evenement === 'ABSENCE') person.absences.push(event);
    people.set(key, person);
  }
  return [...people.values()].sort((first, second) =>
    `${first.employe_nom} ${first.employe_prenom}`.localeCompare(
      `${second.employe_nom} ${second.employe_prenom}`, 'fr',
    ),
  );
}
