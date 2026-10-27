import assert from 'node:assert/strict';
import { createServer } from 'vite';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

globalThis.window = { location: { hostname: '127.0.0.1' } };
globalThis.localStorage = { getItem: () => null };
const server = await createServer({ server: { middlewareMode: true } });
try {
  const { default: Manager } = await server.ssrLoadModule('/modules/module-4/components/PayrollRuleManager.jsx');
  const { default: Editor } = await server.ssrLoadModule('/modules/module-4/components/PayrollRuleEditor.jsx');
  const { ruleForm, rulePayload, rateFields } = await server.ssrLoadModule('/modules/module-4/lib/rules.js');
  const render = (Component, props) => renderToStaticMarkup(React.createElement(Component, props));
  const empty = ruleForm(null);
  for (const [key] of rateFields) assert.equal(empty[key], '');
  assert.equal(empty.plafond_cnss, '');
  const edited = { ...empty, code: 'TEST', nom: 'Règles', source_reference: 'Référence de test', date_debut: '2026-01-01',
    taux_cnss_salarial: '5', taux_cnss_patronal: '16', taux_tpa_patronal: '3', abattement_professionnel: '20', plafond_deduction_retraite: '8',
    tranches_iuts: [{ minimum: '0', maximum: '100000', taux: '0' }, { minimum: '100000', maximum: '', taux: '10' }],
    reductions_iuts_charges: [{ charges: '1', taux: '8' }],
  };
  const payload = rulePayload(edited);
  assert.equal(payload.taux_cnss_salarial, '0.050000');
  assert.equal(payload.tranches_iuts[1].maximum, null);
  assert.equal(payload.tranches_iuts[1].taux, '0.100000');
  assert.equal(payload.reductions_iuts_charges[0].taux, '0.080000');
  assert(!('est_fictif' in payload));
  assert(!('valide' in payload));
  const rule = { ...payload, id: 2, actif: true, valide: false };
  const readonly = render(Manager, { rules: [rule], loading: false, error: '', permissions: {}, onChanged() {} });
  assert(readonly.includes('Consulter les paramètres'));
  assert(!readonly.includes('>Nouvelles règles<'));
  assert(!readonly.includes('>Valider les règles<'));
  const management = render(Manager, { rules: [rule], loading: false, error: '', permissions: { create: true, update: true, delete: true }, onChanged() {} });
  assert(management.includes('>Nouvelles règles<'));
  assert(management.includes('>Modifier<'));
  assert(management.includes('>Valider les règles<'));
  const validated = render(Manager, { rules: [{ ...rule, valide: true }], loading: false, error: '', permissions: { create: true, update: true, delete: true }, onChanged() {} });
  assert(!validated.includes('>Modifier<'));
  assert(!validated.includes('>Supprimer<'));
  assert(validated.includes('Créer une nouvelle version'));
  const editor = render(Editor, { rule: null, mutation: { saving: false, errors: {}, message: '' }, onClose() {}, onSaved() {} });
  for (const label of ['Référence des règles', 'Tranches IUTS', 'Ajouter une tranche', 'Ajouter une réduction', 'CNSS salariale (%)']) assert(editor.includes(label));
  assert(!editor.includes('fictif'));
  console.log('Règles de paie : formulaire, pourcentages, tranches, permissions et validation immuable OK');
} finally {
  await server.close();
}
