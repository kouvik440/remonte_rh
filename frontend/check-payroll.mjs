import assert from 'node:assert/strict';
import { createServer } from 'vite';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

let permissions = [];
const storage = new Map([['access_token', 'test-access']]);
globalThis.window = { location: { hostname: '127.0.0.1', pathname: '/pages/payroll.html' } };
globalThis.localStorage = {
  getItem: (key) => key === 'user' ? JSON.stringify({ permissions }) : storage.get(key) || null,
  setItem: (key, value) => storage.set(key, value), removeItem: (key) => storage.delete(key),
};
const server = await createServer({ server: { middlewareMode: true } });
try {
  const { default: Page } = await server.ssrLoadModule('/modules/module-4/pages/PayrollPage.jsx');
  const { default: List } = await server.ssrLoadModule('/modules/module-4/components/PayrollList.jsx');
  const { default: Editor } = await server.ssrLoadModule('/modules/module-4/components/PayrollEditor.jsx');
  const { default: Action } = await server.ssrLoadModule('/modules/module-4/components/PayrollAction.jsx');
  const { PayrollInformation } = await server.ssrLoadModule('/modules/module-4/components/PayrollDetail.jsx');
  const { availableActions } = await server.ssrLoadModule('/modules/module-4/lib/payroll.js');
  const { apiRequest, downloadApiFile } = await server.ssrLoadModule('/shared/lib/api.js');
  const render = (Component, props = {}) => renderToStaticMarkup(React.createElement(Component, props));
  const payroll = { id: 1, employe: 3, employe_nom: 'Test', employe_prenom: 'Alice', employe_matricule: 'PAY-001', periode: '2026-10', libelle: 'Paie octobre', statut: 'BROUILLON', devise: 'XOF', salaire_net: null };
  assert(render(Page).includes('aucune permission'));
  permissions = ['paie.read'];
  assert(!render(Page).includes('Nouvelle paie'));
  assert(render(Page).includes('payroll.html'));
  const personal = render(List, { payrolls: [payroll], permissions: {}, onDetail() {}, onAction() {} });
  assert(personal.includes('Alice Test'));
  assert(personal.includes('PAY-001'));
  assert(personal.includes('Non calculé'));
  assert(personal.includes('Voir le détail'));
  for (const action of ['Calculer', '>Valider<', '>Supprimer<', '>Modifier<']) assert(!personal.includes(action));
  const manager = { update: true, delete: true };
  assert.deepEqual(availableActions(payroll, manager), ['edit', 'calculate', 'cancel', 'delete']);
  assert.deepEqual(availableActions({ ...payroll, statut: 'CALCULE' }, manager), ['validate', 'cancel']);
  assert.deepEqual(availableActions({ ...payroll, statut: 'VALIDEE', bulletin_generable: true }, manager), ['cancel', 'generate']);
  assert.deepEqual(availableActions({ ...payroll, statut: 'VALIDEE', bulletin_generable: false }, manager), ['cancel']);
  assert.deepEqual(availableActions({ ...payroll, statut: 'PAYE', bulletin_disponible: true }, manager), ['download']);
  assert.deepEqual(availableActions({ ...payroll, statut: 'ANNULE' }, manager), []);
  const mutation = { saving: false, errors: {}, message: '', submit() {} };
  const editor = render(Editor, { payroll: null, employees: [], canChooseEmployee: true, mutation, onClose() {}, onSaved() {} });
  assert(editor.includes('type="month"'));
  assert(!editor.includes('name="salaire_net"'));
  const action = render(Action, { action: 'calculate', payroll, rules: [{ id: 2, actif: true, valide: true, nom: 'Règles validées' }], rulesError: '', mutation, onClose() {}, onSaved() {} });
  assert(action.includes('Règles validées'));
  assert(!action.includes('fictif'));
  assert(action.includes('Charges familiales'));
  assert(render(Action, { action: 'cancel', payroll, rules: [], mutation, onClose() {}, onSaved() {} }).includes('Motif d’annulation'));
  const detail = render(PayrollInformation, { payroll: { ...payroll, detail_calcul: { regle: { code: 'TEST', source_reference: 'Référence' } } } });
  assert(detail.includes('Référence'));
  assert(!detail.includes('<button'));
  const pdf = new Blob(['test-pdf'], { type: 'application/pdf' });
  const calls = [];
  globalThis.fetch = async (url, options) => {
    calls.push({ url, options });
    return new Response(pdf, { status: 200, headers: { 'Content-Type': 'application/pdf' } });
  };
  const binary = await apiRequest('/api/paiements/1/bulletin/', { responseType: 'blob' });
  assert.equal(binary.type, 'application/pdf');
  assert.equal(calls[0].options.headers.Authorization, 'Bearer test-access');
  assert(!('responseType' in calls[0].options));
  let clicked = false;
  globalThis.document = { createElement: () => ({ click() { clicked = true; }, remove() {} }), body: { append() {} } };
  window.setTimeout = (callback) => callback();
  await downloadApiFile('/api/paiements/1/bulletin/', 'test.pdf');
  assert(clicked);
  assert.equal(calls.at(-1).options.headers.Accept, '*/*');
  storage.set('refresh_token', 'test-refresh');
  let requestCount = 0;
  globalThis.fetch = async (url, options) => {
    requestCount++;
    if (url.endsWith('/refresh/')) return Response.json({ access: 'renewed-access' });
    if (options.headers.Authorization === 'Bearer test-access') return Response.json({ detail: 'Expired' }, { status: 401 });
    return new Response(pdf, { headers: { 'Content-Type': 'application/pdf' } });
  };
  assert.equal((await apiRequest('/api/paiements/1/bulletin/', { responseType: 'blob' })).type, 'application/pdf');
  assert.equal(requestCount, 3);
  globalThis.fetch = async () => Response.json({ detail: 'Accès refusé' }, { status: 403 });
  await assert.rejects(apiRequest('/api/paiements/1/bulletin/', { responseType: 'blob' }), (error) => error.status === 403 && error.message === 'Accès refusé');
  console.log('Module 4 : permissions, statuts, formulaires, détail en lecture seule, PDF authentifié et renouvellement JWT OK');
} finally {
  await server.close();
}
