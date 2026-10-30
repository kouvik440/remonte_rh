import assert from 'node:assert/strict';
import { createServer } from 'vite';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

let permissions = [];
globalThis.window = { location: { hostname: '127.0.0.1' } };
globalThis.localStorage = { getItem: (key) => key === 'access_token' ? 'test-token' : key === 'user' ? JSON.stringify({ permissions }) : null };
const server = await createServer({ server: { middlewareMode: true, hmr: false }, optimizeDeps: { noDiscovery: true } });
try {
  const { default: Page } = await server.ssrLoadModule('/modules/module-6/pages/TgmPage.jsx');
  const { default: Employees } = await server.ssrLoadModule('/modules/module-6/components/TgmEmployees.jsx');
  const { default: Costs } = await server.ssrLoadModule('/modules/module-6/components/TgmProjectCosts.jsx');
  const { default: Simulation } = await server.ssrLoadModule('/modules/module-6/components/TgmSimulation.jsx');
  const { validatePeriod, reportPaths, amount } = await server.ssrLoadModule('/modules/module-6/lib/tgm.js');
  const render = (Component, props = {}) => renderToStaticMarkup(React.createElement(Component, props));
  assert(render(Page).includes('permission paie.read'));
  assert(!render(Page).includes('href="/pages/tgm.html"'));
  permissions = ['paie.read'];
  assert(render(Page).includes('Taux journalier et horaire moyen'));
  assert(render(Page).includes('Chargement des taux'));
  assert.deepEqual(validatePeriod({ start: '2026-01', end: '2026-10' }), {});
  assert(validatePeriod({ start: '2026-11', end: '2026-10' }).end);
  assert(validatePeriod({ start: '0000-01', end: '2026-10' }).start);
  for (const [period, lastDay] of [['2024-02', '29'], ['2026-02', '28'], ['1900-02', '28'], ['2000-02', '29'], ['0001-02', '28'], ['9999-12', '31']]) {
    const paths = reportPaths({ start: period, end: period });
    assert.equal(new URLSearchParams(paths.costs.split('?')[1]).get('date_fin'), `${period}-${lastDay}`);
  }
  const row = { employe_id: 1, employe_nom: 'Test', employe_prenom: 'TGM', matricule: 'TGM-001', devise: 'XOF', periodes: ['2026-10'], jours_ouvres_previsionnels: 22,
    heures_previsionnelles: '132.00', salaire_brut_total: '220000.00', cout_charge_total: '264000.00', taux_journalier_brut: '10000.00', taux_journalier_charge: '12000.00', taux_horaire_brut: '1666.67', taux_horaire_charge: '2000.00' };
  const employees = render(Employees, { report: { employes: [row], note: 'Hypothèses' } });
  for (const text of ['TGM-001', amount('2000'), 'tabindex="0"', 'scope="row"', 'Hypothèses']) assert(employees.includes(text), text);
  assert(render(Employees, { report: { employes: [], note: '' } }).includes('Aucune paie'));
  const incomplete = { heures_validees: '3.00', heures_sans_tgm: '1.00', cout_calculable: '4000.00', cout_estime: null, cout_complet: false };
  const project = { ...incomplete, projet_id: 1, projet_code: 'P-001', projet_nom: 'Prestation', employes: [{ ...row, ...incomplete }], taches: [] };
  const costs = render(Costs, { report: { totaux: incomplete, projets: [project], note: '', formule: 'Formule' } });
  assert(costs.includes('Estimation incomplète'));
  assert(costs.includes('TGM-001'));
  assert(costs.includes('<details'));
  assert(costs.includes(amount('4000')));
  const simulation = render(Simulation, { projects: [project], period: { start: '2026-10', end: '2026-10' } });
  assert(simulation.includes('Chiffre d’affaires de la période (XOF)'));
  assert(simulation.includes('Calculer la marge'));
  assert(render(Simulation, { projects: [], period: {} }).includes('nécessite un projet'));
  const { default: Overview } = await server.ssrLoadModule('/modules/module-6/components/TgmOverview.jsx');
  const { default: ProductiveSimulation } = await server.ssrLoadModule('/modules/module-6/components/TgmProductiveSimulation.jsx');
  const filtered = new URLSearchParams(reportPaths({ start: '2026-01', end: '2026-10', department: '3', employee: '4' }).rates.split('?')[1]);
  assert.equal(filtered.get('departement'), '3');
  assert.equal(filtered.get('employe'), '4');
  const department = { departement_id: 1, departement: 'Finance', devise: 'XOF', employes: 2,
    cout_charge_total: '22000', taux_journalier_charge: '1000', taux_horaire_charge: null };
  const overview = render(Overview, { report: { par_departement: [department] } });
  assert(overview.includes('Finance'));
  assert(overview.includes('Indisponible'));
  assert(overview.includes('mass-bar-validated'));
  assert(!overview.includes('NaN'));
  assert.equal(render(Overview, { report: { par_departement: [] } }), '');
  assert(employees.includes('Rechercher'));
  assert(employees.includes('Pagination'));
  assert(employees.includes('Trier par'));
  const productive = render(ProductiveSimulation, { period: { start: '2026-01', end: '2026-10' }, employees: [row] });
  assert(productive.includes('Jours productifs'));
  assert(productive.includes('Heures productives'));
  assert(productive.includes('max="100000"'));
  assert(productive.includes('TGM-001'));
  assert(render(ProductiveSimulation, { period: {}, employees: [] }).includes('Aucun employé'));
  console.log('Module 6 : permissions, périodes, calendrier, taux, coûts incomplets et simulation vérifiés.');
} finally { await server.close(); }
