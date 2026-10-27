import assert from 'node:assert/strict';
import { createServer } from 'vite';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { homePath } from './src/shared/lib/homePath.js';

assert.equal(homePath({ permissions: [] }), '/pages/timesheets.html');
assert.equal(homePath({ permissions: ['conge.read', 'demande_absence.read', 'coordonnees_bancaires.read'] }), '/pages/timesheets.html');
assert.equal(homePath({ permissions: ['employe.read'] }), '/pages/employees.html');
assert.equal(homePath({ permissions: ['feuille_temps.decide'] }), '/pages/timesheets.html');
assert.equal(homePath({ permissions: ['paie.read'], roles: ['FRONTEND_MODULE_6_TGM'] }), '/pages/tgm.html');
assert.equal(homePath({ permissions: ['paie.read'] }), '/pages/payroll-mass.html');
assert.equal(homePath({ permissions: ['paie.update'] }), '/pages/payroll.html');
assert.equal(homePath({ permissions: ['demande_absence.update'] }), '/pages/leaves.html');
assert.equal(homePath({ permissions: ['coordonnees_bancaires.manage'] }), '/pages/records.html');
let permissions = ['demande_absence.read', 'solde_conge.read', 'coordonnees_bancaires.read'];
globalThis.window = { location: { hostname: '127.0.0.1' } };
globalThis.localStorage = { getItem: (key) => key === 'user' ? JSON.stringify({ permissions }) : null };
const server = await createServer({ server: { middlewareMode: true, hmr: false }, optimizeDeps: { noDiscovery: true } });
try {
  const { default: Layout } = await server.ssrLoadModule('/shared/components/AppLayout.jsx');
  const markup = () => renderToStaticMarkup(React.createElement(Layout, { active: 'timesheets' }));
  const employee = markup();
  assert(!employee.includes('href="/pages/employees.html"'));
  for (const path of ['timesheets', 'leaves', 'records']) assert(employee.includes(`href="/pages/${path}.html"`));
  for (const path of ['roles', 'tgm', 'payroll', 'payroll-mass']) assert(!employee.includes(`href="/pages/${path}.html"`));
  permissions = ['employe.read'];
  assert(markup().includes('href="/pages/employees.html"'));
  console.log('Accueil selon les droits et navigation personnelle sans accès RH global vérifiés.');
} finally { await server.close(); }
