import assert from 'node:assert/strict';
import { createServer } from 'vite';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

let permissionCodes = [];
globalThis.window = { location: { hostname: '127.0.0.1' } };
globalThis.localStorage = { getItem: (key) => key === 'user' ? JSON.stringify({ permissions: permissionCodes }) : null };
const server = await createServer({ server: { middlewareMode: true } });
try {
  const { default: Types } = await server.ssrLoadModule('/modules/module-2/components/LeaveTypeManager.jsx');
  const { default: Balances } = await server.ssrLoadModule('/modules/module-2/components/LeaveBalanceManager.jsx');
  const types = [{ id: 1, code: 'CP', libelle: 'Congé payé', jours_par_annee: 30, actif: true, est_payant: true }];
  const balances = [{ id: 1, employe: 1, employe_prenom: 'Alice', employe_nom: 'Test', employe_matricule: 'TEST-001', type_conge_libelle: 'Congé payé', annee: 2026, acquis: 30, pris: 5, en_attente: 2, disponible: 23 }];
  const renderTypes = () => renderToStaticMarkup(React.createElement(Types, { types, onChanged() {} }));
  const renderBalances = () => renderToStaticMarkup(React.createElement(Balances, { types, balances, year: 2026, onYearChange() {}, onChanged() {} }));
  assert(!renderTypes().includes('Créer un type'));
  assert(!renderTypes().includes('>Modifier</button>'));
  assert(!renderBalances().includes('Modifier les jours acquis'));
  permissionCodes = ['conge.create', 'conge.update', 'conge.delete', 'solde_conge.create', 'solde_conge.update', 'employe.read'];
  assert(renderTypes().includes('Créer un type'));
  assert(renderTypes().includes('>Modifier</button>'));
  assert(renderTypes().includes('>Supprimer</button>'));
  assert(!renderTypes().includes('CP ·'), 'Le code technique ne doit pas être présenté avec le libellé');
  const html = renderBalances();
  assert(!html.includes('Attribuer des jours acquis')); 
  assert(!html.includes('Modifier les jours acquis')); 
  assert(html.includes('Alice Test'));
  assert(html.includes('TEST-001'));
  console.log('Gestion des congés : rendu lecture/gestion et identité des soldes OK');
} finally {
  await server.close();
}
