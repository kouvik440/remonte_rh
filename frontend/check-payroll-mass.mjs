import assert from 'node:assert/strict';
import { createServer } from 'vite';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

let permissions = [];
const storage = new Map([['access_token', 'test-access']]);
globalThis.window = { location: { hostname: '127.0.0.1' }, setTimeout: (callback) => callback() };
globalThis.localStorage = {
  getItem: (key) => key === 'user' ? JSON.stringify({ permissions }) : storage.get(key) || null,
  setItem: (key, value) => storage.set(key, value), removeItem: (key) => storage.delete(key),
};
const server = await createServer({ server: { middlewareMode: true }, optimizeDeps: { noDiscovery: true } });
try {
  const { default: Page } = await server.ssrLoadModule('/modules/module-5/pages/PayrollMassPage.jsx');
  const { default: Totals } = await server.ssrLoadModule('/modules/module-5/components/MassTotals.jsx');
  const { default: Evolution } = await server.ssrLoadModule('/modules/module-5/components/MassEvolution.jsx');
  const { default: Breakdown } = await server.ssrLoadModule('/modules/module-5/components/MassBreakdown.jsx');
  const { default: Filters } = await server.ssrLoadModule('/modules/module-5/components/MassFilters.jsx');
  const { analysisQuery, massExportPath, validateFilters, money, exportTypes } = await server.ssrLoadModule('/modules/module-5/lib/payrollMass.js');
  const { downloadApiFile } = await server.ssrLoadModule('/shared/lib/api.js');
  const render = (Component, props = {}) => renderToStaticMarkup(React.createElement(Component, props));
  assert(render(Page).includes('permission paie.read'));
  assert(!render(Page).includes('payroll-mass.html'));
  permissions = ['paie.read'];
  const page = render(Page);
  assert(page.includes('payroll-mass.html'));
  assert(page.includes('Afficher l’analyse'));
  assert(page.includes('Chargement de l’analyse'));
  assert(!page.includes('Nouvelle paie'));
  assert(page.includes('nécessite la permission departement.read'));
  const filters = { start: '2025-12', end: '2026-10', department: '7', granularity: 'annuelle' };
  const query = new URLSearchParams(analysisQuery(filters, { format_fichier: 'xlsx' }));
  assert.equal(query.get('departement'), '7');
  assert.equal(query.get('periode_debut'), '2025-12');
  assert.equal(query.get('format_fichier'), 'xlsx');
  assert(!query.has('granularite'));
  assert(!new URLSearchParams(analysisQuery({ ...filters, department: '' })).has('departement'));
  assert.deepEqual(validateFilters(filters), {});
  const filterMarkup = render(Filters, { applied: filters, departments: [{ id: 7, nom: 'Direction RH' }], canReadDepartments: true, departmentError: '', busy: false, onApply() {} });
  assert.equal((filterMarkup.match(/role="combobox"/g) || []).length, 2);
  const labels = [...filterMarkup.matchAll(/<label[^>]*for="([^"]+)"/g)].map((match) => match[1]);
  assert.equal(labels.length, 2);
  for (const id of labels) assert(filterMarkup.includes(`id="${id}"`));
  assert(filterMarkup.includes('data-slot="card"'));
  assert(validateFilters({ ...filters, start: '2027-01' }).end);
  assert(validateFilters({ ...filters, start: '0000-01' }).start);
  assert(validateFilters({ ...filters, end: '2026-13' }).end);
  const totals = { paies_validees: 1, paies_payees: 2, brut_valide: '123.00', net_valide: '111.25', cotisations_validees: '12.00', cout_employeur_valide: '145.00', brut_paye: '234.00', net_paye: '222.50', cotisations_payees: '23.00', cout_employeur_paye: '267.00' };
  const summary = render(Totals, { totals });
  assert(summary.includes(money('111.25')));
  assert(summary.includes(money('222.50')));
  assert(!summary.includes(money('333.75')));
  assert(summary.includes('1 paie(s)'));
  assert(summary.includes('2 paie(s)'));
  assert.equal((summary.match(/data-slot="card"/g) || []).length, 2);
  const annual = render(Evolution, { data: { granularite: 'annuelle', evolution: [{ ...totals, annee: '2026', employes: 2 }] } });
  assert(annual.includes('Évolution annuelle'));
  assert(annual.includes('2026'));
  assert(annual.includes(money('111.25')));
  assert(annual.includes('Employés distincts'));
  assert(annual.includes('data-slot="table-container"'));
  assert(annual.includes('tabindex="0"'));
  assert(annual.includes('scope="row"'));
  assert.equal((annual.match(/<svg /g) || []).length, 3);
  for (const text of ['Brut validé', 'Brut payé', 'Coût employeur', 'Cotisations', money('145.00'), money('267.00'), money('12.00'), money('23.00')]) assert(annual.includes(text), text);
  const monthly = render(Evolution, { data: { granularite: 'mensuelle', evolution: [{ ...totals, periode: '2026-10', employes: 2 }] } });
  assert(monthly.includes('Évolution mensuelle'));
  assert.equal((monthly.match(/<svg /g) || []).length, 3);
  const zeros = Object.fromEntries(Object.keys(totals).map((key) => [key, 0]));
  const zeroChart = render(Evolution, { data: { granularite: 'mensuelle', evolution: [{ ...zeros, periode: '2026-10', employes: 0 }] } });
  assert(!zeroChart.includes('NaN') && !zeroChart.includes('Infinity'));
  assert(render(Evolution, { data: { granularite: 'mensuelle', evolution: [] } }).includes('Aucune évolution'));
  assert(render(Breakdown, { title: 'Par département', rows: [], labelKey: 'departement', idKey: 'departement_id' }).includes('Aucune paie'));
  for (const [title, labelKey, idKey] of [['Par département', 'departement', 'departement_id'], ['Par type de contrat', 'type_contrat', 'type_contrat_id']]) {
    const breakdown = render(Breakdown, { title, rows: [{ ...totals, [labelKey]: 'Administration', [idKey]: '7' }], labelKey, idKey });
    for (const text of ['Brut validé', 'Brut payé', 'Cotisations validées', 'Cotisations payées', money('123.00'), money('234.00')]) assert(breakdown.includes(text), text);
  }
  let clicked = 0;
  const calls = [];
  globalThis.document = { createElement: () => ({ click() { clicked++; }, remove() {} }), body: { append() {} } };
  for (const granularity of ['mensuelle', 'annuelle']) for (const [format, contentType] of Object.entries(exportTypes)) {
    globalThis.fetch = async (url, options) => {
      calls.push({ url, options });
      return new Response('test-export', { headers: { 'Content-Type': format === 'csv' ? 'text/csv; charset=utf-8' : contentType } });
    };
    await downloadApiFile(massExportPath({ ...filters, granularity }, format), `test.${format}`, contentType);
    assert.equal(calls.at(-1).options.headers.Authorization, 'Bearer test-access');
    assert.equal(calls.at(-1).options.headers.Accept, '*/*');
    const exportQuery = new URL(calls.at(-1).url).searchParams;
    assert.equal(exportQuery.get('granularite'), granularity);
    assert.equal(exportQuery.get('departement'), '7');
  }
  assert.equal(clicked, 6);
  globalThis.fetch = async () => Response.json({ detail: 'Accès refusé' }, { status: 403 });
  await assert.rejects(downloadApiFile('/export/', 'test.csv', 'text/csv'), (error) => error.status === 403);
  globalThis.fetch = async () => new Response('<html>Erreur</html>', { headers: { 'Content-Type': 'text/html' } });
  await assert.rejects(downloadApiFile('/export/', 'test.csv', 'text/csv'), /format de fichier/);
  assert.equal(clicked, 6);
  console.log('Module 5 : permissions, filtres, totaux séparés, évolution et exports authentifiés vérifiés.');
} finally { await server.close(); }
