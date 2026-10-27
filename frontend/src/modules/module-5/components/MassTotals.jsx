import React from 'react';
import { money } from '../lib/payrollMass.js';
import MassPanel from './MassPanel.jsx';

const groups = [
  { title: 'Paies validées, en attente de paiement', count: 'paies_validees', fields: ['brut_valide', 'net_valide', 'cotisations_validees', 'cout_employeur_valide'] },
  { title: 'Paies payées', count: 'paies_payees', fields: ['brut_paye', 'net_paye', 'cotisations_payees', 'cout_employeur_paye'] },
];
const labels = ['Salaire brut', 'Salaire net', 'Cotisations', 'Coût employeur'];

export default function MassTotals({ totals }) {
  return <div className="mass-totals">{groups.map((group) => <MassPanel key={group.count} title={group.title} description={`${totals[group.count]} paie(s) sur la période`}>
    <dl className="mass-metrics">{group.fields.map((key, index) => <div key={key}><dt>{labels[index]}</dt><dd>{money(totals[key])}</dd></div>)}</dl>
  </MassPanel>)}</div>;
}
