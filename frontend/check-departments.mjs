import assert from 'node:assert/strict';
import { createServer } from 'vite';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

let permissions = [];
globalThis.window = { location: { hostname: '127.0.0.1' } };
globalThis.localStorage = { getItem: (key) => key === 'user' ? JSON.stringify({ permissions }) : key === 'access_token' ? 'test-only' : null };
const server = await createServer({ server: { middlewareMode: true } });
try {
  const { default: Page } = await server.ssrLoadModule('/modules/module-1/pages/DepartmentsPage.jsx');
  const { default: List } = await server.ssrLoadModule('/modules/module-1/components/DepartmentList.jsx');
  const { default: Editor } = await server.ssrLoadModule('/modules/module-1/components/DepartmentEditor.jsx');
  const render = (component, props = {}) => renderToStaticMarkup(React.createElement(component, props));
  const departments = [{ id: 1, nom: 'Direction RH', code: 'RH' }];
  const props = { departments, busy: false, onEdit() {}, onDelete() {} };
  assert(render(Page).includes('Vous n’avez pas accès'));
  assert(!render(Page).includes('href="/pages/departments.html"'));
  permissions = ['departement.read'];
  assert(render(Page).includes('href="/pages/departments.html"'));
  assert(!render(Page).includes('Nouveau département'));
  assert(!render(List, props).includes('<button'));
  assert(render(List, props).includes('Direction RH'));
  assert(render(List, { ...props, departments: [] }).includes('Aucun département'));
  permissions.push('departement.create', 'departement.update', 'departement.delete');
  assert(render(Page).includes('Nouveau département'));
  const list = render(List, props);
  assert(list.includes('>Modifier<') && list.includes('>Supprimer<'));
  const busy = render(List, { ...props, busy: true });
  assert.equal((busy.match(/disabled=""/g) || []).length, 2);
  const mutation = { errors: { nom: ['Ce nom existe déjà.'] }, message: '', saving: false };
  const form = render(Editor, { department: departments[0], mutation, onClose() {}, onSaved() {} });
  for (const text of ['Nom du département', 'Code du département', 'value="Direction RH"', 'value="RH"', 'Ce nom existe déjà.', 'aria-invalid="true"', 'aria-describedby=']) assert(form.includes(text), text);
  console.log('Départements : accès, navigation, boutons CRUD, liste vide, blocage et erreurs accessibles OK');
} finally {
  await server.close();
}
