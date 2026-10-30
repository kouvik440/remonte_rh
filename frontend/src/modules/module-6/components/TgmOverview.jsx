import React from 'react';
import TgmPanel from './TgmPanel.jsx';
import { amount } from '../lib/tgm.js';

export default function TgmOverview({ report }) {
  const rows = report.par_departement || [];
  if (!rows.length) return null;
  return <TgmPanel title="Comparaison des départements" description="Taux chargés pondérés par les jours et les heures prévus. Les devises restent séparées.">
    <div className="tgm-simulation-results">{rows.map((row) => <dl key={`${row.departement_id}-${row.devise}`}>
      <dt>{row.departement} · {row.employes} employé(s) · {row.devise}</dt>
      <dd>{amount(row.cout_charge_total, row.devise)}</dd>
      <p className="tgm-note">Coût journalier : {amount(row.taux_journalier_charge, row.devise)}<br />Coût horaire : {amount(row.taux_horaire_charge, row.devise)}</p>
    </dl>)}</div>
    {Array.from(new Set(rows.map((row) => row.devise))).map((currency) => {
      const group = rows.filter((row) => row.devise === currency);
      const max = Math.max(1, ...group.map((row) => Number(row.taux_journalier_charge) || 0));
      return <figure key={currency} style={{ margin: '16px 0', overflowX: 'auto' }}>
        <figcaption>Coût journalier chargé · {currency}</figcaption>
        <svg viewBox={`0 0 640 ${group.length * 50 + 30}`} style={{ width: '100%', minWidth: 320 }} role="img" aria-label={`Comparaison des taux journaliers par département en ${currency}`}>
          {group.map((row, index) => <g key={row.departement_id}>
            <title>{`${row.departement} : ${amount(row.taux_journalier_charge, currency)}`}</title>
            <text x="0" y={index * 50 + 18} fill="var(--app-ink)" fontSize="12">{row.departement}</text>
            <rect className="mass-bar-validated" x="0" y={index * 50 + 25} width={Number(row.taux_journalier_charge || 0) / max * 500} height="14" rx="3" />
            <text x="510" y={index * 50 + 37} fill="var(--app-ink)" fontSize="11">{amount(row.taux_journalier_charge, currency)}</text>
          </g>)}
        </svg>
      </figure>;
    })}
  </TgmPanel>;
}
