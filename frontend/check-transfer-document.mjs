import assert from 'node:assert/strict';
import { createServer } from 'vite';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

globalThis.window = { location: { hostname: '127.0.0.1' } };
globalThis.localStorage = { getItem: () => null };
const server = await createServer({ server: { middlewareMode: true }, optimizeDeps: { noDiscovery: true } });
try {
  const { TransferDocumentFields } = await server.ssrLoadModule('/modules/module-4/components/TransferDocumentDialog.jsx');
  const { transferActions } = await server.ssrLoadModule('/modules/module-4/lib/transfers.js');
  const { TransferList } = await server.ssrLoadModule('/modules/module-4/components/TransferOrders.jsx');
  const render = (Component, props) => renderToStaticMarkup(React.createElement(Component, props));
  const order = { id: 1, employe: 1, employe_nom: 'Test', periode: '2026-10', statut: 'GENERE' };
  const permissions = { update: true, delete: true, payrollRead: true, document: true };
  assert(transferActions(order, permissions, []).includes('document'));
  assert(!transferActions(order, { ...permissions, document: false }, []).includes('document'));
  const archived = { ...order, document_disponible: true };
  const actions = transferActions(archived, permissions, []);
  assert(actions.includes('download_document'));
  assert(!actions.includes('document'));
  assert(!actions.includes('edit'));
  assert(!actions.includes('delete'));
  assert(!transferActions({ ...order, statut: 'TRAITE' }, permissions, []).includes('document'));
  const list = render(TransferList, { orders: [order], payrolls: [], permissions, onDetail() {}, onAction() {} });
  assert(list.includes('Générer l’ordre PDF'));
  const form = { coordonnees_bancaires: '', donneur_nom: '', donneur_adresse: '', donneur_telephone: '', banque: '', agence: '', compte_debit: '', lieu: '', signataire: '', fonction_signataire: '', motif: '', date_execution: '2026-10-30', canal: 'BANQUE' };
  const context = { comptes: [{ id: 1, banque: 'Banque bénéficiaire', compte_masque: '•••• 0090', rib_valide: true }] };
  const html = render(TransferDocumentFields, { form, change: () => () => {}, context, mutation: { errors: {} }, busy: false });
  for (const text of ['Compte bancaire du bénéficiaire', 'RIB complet du compte à débiter', 'Entreprise / titulaire du compte', 'Nom du signataire', 'Date d’exécution', 'Mode de virement']) assert(html.includes(text));
  assert(html.includes('•••• 0090'));
  assert(!html.includes('name="montant"'));
  assert(render(TransferDocumentFields, { form, change: () => () => {}, context: { comptes: [] }, mutation: { errors: {} }, busy: false }).includes('Ajoutez un RIB UEMOA complet'));
  console.log('Ordre PDF BF : génération/téléchargement autorisés, instructions figées, formulaire et comptes masqués OK');
} finally {
  await server.close();
}
