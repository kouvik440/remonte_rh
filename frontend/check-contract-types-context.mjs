import assert from 'node:assert/strict';
import { createServer } from 'vite';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

let permissions = [];
globalThis.window = { location: { hostname: '127.0.0.1' } };
globalThis.localStorage = { getItem: (key) => key === 'user' ? JSON.stringify({ permissions }) : key === 'access_token' ? 'test-only' : null };
const server = await createServer({ server: { middlewareMode: true } });
try {
  const { ContractTypeList } = await server.ssrLoadModule('/modules/module-1/components/ContractTypeManager.jsx');
  const { default: TypeEditor } = await server.ssrLoadModule('/modules/module-1/components/ContractTypeEditor.jsx');
  const { default: EmployeesPage } = await server.ssrLoadModule('/modules/module-1/pages/EmployeesPage.jsx');
  const { PayrollContractInformation, default: Preview } = await server.ssrLoadModule('/modules/module-4/components/PayrollContractPreview.jsx');
  const { default: PayrollEditor } = await server.ssrLoadModule('/modules/module-4/components/PayrollEditor.jsx');
  const render = (Component, props = {}) => renderToStaticMarkup(React.createElement(Component, props));
  const types = [{ id: 1, type: 'CDD', description: 'Description du type' }];
  const readonly = render(ContractTypeList, { types, onEdit() {}, onDelete() {} });
  assert(readonly.includes('CDD'));
  assert(!readonly.includes('<button'));
  permissions = ['employe.read', 'type_contrat.read', 'type_contrat.create', 'type_contrat.update', 'type_contrat.delete'];
  assert(render(EmployeesPage).includes('>Types de contrat<'));
  const management = render(ContractTypeList, { types, onEdit() {}, onDelete() {} });
  assert(management.includes('>Modifier<'));
  assert(management.includes('>Supprimer<'));
  const mutation = { errors: {}, message: '', saving: false, submit() {} };
  const typeForm = render(TypeEditor, { type: null, mutation, onClose() {}, onSaved() {} });
  assert(typeForm.includes('Libellé du type'));
  assert(typeForm.includes('Description (facultative)'));
  assert(typeForm.includes('required=""'));
  const contract = { id: 1, salaire_base: '325000.50', heures_journalieres: '8.00', statut: 'EN_COURS', date_debut: '2026-01-01', date_fin: null, types_libelles: ['CDD'] };
  const context = { state: 'READY', contracts: [contract] };
  const information = render(PayrollContractInformation, { context });
  for (const text of ['Salaire mensuel contractuel', 'Heures journalières', 'CDD', 'En cours', '2026-01-01', '8.00 h/jour', '325']) assert(information.includes(text));
  assert(!information.includes('<input'));
  assert(render(PayrollContractInformation, { context: { state: 'MISSING', contracts: [] } }).includes('Aucun contrat'));
  const overlap = render(PayrollContractInformation, { context: { state: 'AMBIGUOUS', contracts: [contract, { ...contract, id: 2 }] } });
  assert(overlap.includes('Plusieurs contrats'));
  assert(overlap.includes('role="alert"'));
  assert(render(Preview, { employeeId: '', period: '2026-10' }).includes('Choisissez un employé'));
  const payrollForm = render(PayrollEditor, { payroll: null, employees: [], canChooseEmployee: true, mutation, onClose() {}, onSaved() {} });
  assert(payrollForm.includes('Contrat pour la période de paie'));
  console.log('Types de contrat et aperçu de paie : accès, formulaires, attributs en lecture seule et contrats absents/multiples OK');
} finally {
  await server.close();
}
