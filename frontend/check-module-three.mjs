import assert from 'node:assert/strict';
import { createServer } from 'vite';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

let permissions = [];
globalThis.window = { location: { hostname: '127.0.0.1', pathname: '/pages/records.html' } };
globalThis.localStorage = { getItem: (key) => key === 'user' ? JSON.stringify({ id: 1, permissions }) : key === 'access_token' ? 'test-token' : null };
const server = await createServer({ server: { middlewareMode: true } });
try {
  const { default: Page } = await server.ssrLoadModule('/modules/module-3/pages/EmployeeRecordsPage.jsx');
  const { default: Manager } = await server.ssrLoadModule('/modules/module-3/components/RecordManager.jsx');
  const { default: Editor } = await server.ssrLoadModule('/modules/module-3/components/RecordEditor.jsx');
  const { fieldsFor, formFor } = await server.ssrLoadModule('/modules/module-3/lib/resources.js');
  const bank = { id: 1, iban: 'FICTIVE12345678901234', banque: 'Banque fictive', employe_nom: 'Test', employe_prenom: 'Alice', date_modification: '2026-10-23T10:00:00Z' };
  const options = { employees: [{ id: 1, nom: 'Test', prenom: 'Alice', matricule: 'TEST-001' }], types: [{ id: 1, libelle: 'Attestation', is_active: true }] };
  const renderManager = (kind, records) => renderToStaticMarkup(React.createElement(Manager, { kind, records, ...options, loading: false, error: '', onChanged() {} }));
  assert(renderToStaticMarkup(React.createElement(Page)).includes('aucune permission'));
  permissions = ['coordonnees_bancaires.read'];
  const personal = renderManager('bank', [bank]);
  assert(!personal.includes(bank.iban));
  assert(personal.includes('1234'));
  assert(!personal.includes('>Modifier</button>'));
  const employeePage = renderToStaticMarkup(React.createElement(Page));
  assert(!employeePage.includes('données fictives'));
  assert(!employeePage.includes("Le chiffrement du stockage bancaire n'est pas encore activé"));
  assert(!employeePage.includes('Références documentaires'));
  assert(!employeePage.includes('>Types de document</button>'));
  permissions = ['coordonnees_bancaires.read', 'coordonnees_bancaires.create', 'coordonnees_bancaires.update', 'coordonnees_bancaires.delete', 'coordonnees_bancaires.manage', 'document.manage', 'document.read', 'document.create', 'document.update', 'document.delete', 'type_document.read', 'employe.read'];
  const management = renderManager('bank', [bank]);
  assert(management.includes('>Modifier</button>'));
  assert(management.includes('>Supprimer</button>'));
  const fields = fieldsFor('bank', options, false);
  const editorHtml = renderToStaticMarkup(React.createElement(Editor, { fields, form: formFor(fields, null), setForm() {}, mutation: { saving: false, errors: {} }, onSave() {}, onCancel() {} }));
  assert(editorHtml.includes('Banque'));
  assert(editorHtml.includes('IBAN'));
  assert(editorHtml.includes('Employé'));
  assert(!editorHtml.includes('fictif'));
  assert(!editorHtml.includes('fictive'));
  assert(!editorHtml.includes('Type de document'));
  assert(!editorHtml.includes('type="file"'));
  console.log('Module 3 : accès bancaire, masquage, formulaire et retrait des sections documentaires OK');
} finally {
  await server.close();
}
