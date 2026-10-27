import assert from 'node:assert/strict';
import { groupPlanningPeople, indexPlanningDays } from './src/modules/module-2/lib/planning.js';

const presence = {
  id: 'presence-1', employe_id: 1, employe_nom: 'Test', employe_prenom: 'Alice',
  type_evenement: 'PRESENCE_PREVUE', date_debut: '2026-10-01', date_fin: '2026-10-01',
};
const absence = { ...presence, id: 'absence-1', employe_id: '1', type_evenement: 'ABSENCE', date_fin: '2026-10-03' };
const people = groupPlanningPeople([presence, absence]);
assert.equal(people.length, 1, 'Une personne ne doit compter qu’une fois');
assert.equal(people[0].absences.length, 1, 'L’absence prime sur une présence prévue');
const days = indexPlanningDays([absence], '2026-10-02', '2026-10-02');
assert.deepEqual(Object.keys(days), ['2026-10-02'], 'La période doit être limitée au mois affiché');
assert.equal(days['2026-10-02'][0].id, absence.id);
assert.deepEqual(groupPlanningPeople([]), []);
console.log('Planning: regroupement des personnes et limites des dates OK');
