import React from 'react';
import MassPanel from './MassPanel.jsx';
import { money, periodLabel } from '../lib/payrollMass.js';

const metrics = [['brut', 'Masse salariale brute'], ['net', 'Masse salariale nette'], ['cout_employeur', 'Coût employeur total'], ['cout_moyen_employe', 'Coût moyen par employé'], ['charges_patronales', 'Charges patronales'], ['cotisations_salariales', 'Cotisations salariales']];
export default function MassAnalytics({ report }) {
  if (!report.indicateurs) return null;
  const comparison = report.comparaison;
  const rows = report.evolution_mensuelle;
  const max = Math.max(1, ...rows.map(row => Number(row.cout_employeur_valide) + Number(row.cout_employeur_paye)));
  const point = (row, index, key) => `${50 + index * 600 / Math.max(1, rows.length - 1)},${190 - (Number(row[`${key}_valide`]) + Number(row[`${key}_paye`])) / max * 160}`;
  const departments = report.par_departement.map(row => ({ label: row.departement, value: Number(row.cout_employeur_valide) + Number(row.cout_employeur_paye) })).sort((a,b) => b.value-a.value);
  const segments = departments.slice(0,4);
  if (departments.length > 4) segments.push({ label: 'Autres', value: departments.slice(4).reduce((sum,row)=>sum+row.value,0) });
  const total = segments.reduce((sum,row)=>sum+row.value,0);
  let offset = 0;
  return <>
    <div className="mass-analytics-kpis">{metrics.map(([key,label]) => {
      const variation = comparison?.variations?.[key];
      return <MassPanel key={key} title={label}><p className="mass-kpi-value">{money(report.indicateurs[key])}</p>
        {variation && variation.ecart !== null ? <p className="mass-note">{Number(variation.ecart) > 0 ? '↑ +' : Number(variation.ecart) < 0 ? '↓ ' : '= '}{money(variation.ecart)} · {variation.taux === null ? 'Base précédente nulle : taux indisponible' : `${Number(variation.taux) > 0 ? '+' : ''}${Number(variation.taux).toLocaleString('fr-FR')} %`}</p> : null}
      </MassPanel>;
    })}</div>
    {comparison ? <p className="mass-note">Comparaison avec la période du {periodLabel(comparison.periode_debut)} au {periodLabel(comparison.periode_fin)}. {report.indicateurs.employes} employé(s) distinct(s). Une hausse de coût n’indique pas à elle seule une amélioration.</p> : null}
    <div className="mass-analytics-charts">
      <MassPanel title="Tendances salariales" description="Brut et coût employeur · valeurs détaillées au survol et dans les tableaux">
        {!rows.length ? <p className="leave-state">Aucune évolution disponible.</p> : <div className="mass-trend-chart"><svg viewBox="0 0 700 240" role="img" aria-label="Évolution mensuelle du brut et du coût employeur">
          {[0,1,2,3].map(step => <g key={step}><line x1="50" x2="660" y1={190-step*53} y2={190-step*53} className="mass-chart-grid"/><text x="4" y={195-step*53}>{Math.round(max*step/3/1000)}k</text></g>)}
          {rows.map((row,index) => {const value=Number(row.cotisations_validees)+Number(row.cotisations_payees);const x=50+index*600/Math.max(1,rows.length-1);return <rect key={row.periode} x={x-7} y={190-value/max*160} width="14" height={value/max*160} fill="var(--ui-muted-foreground)" opacity="0.4" tabIndex="0"><title>{`${periodLabel(row.periode)} : Cotisations ${money(value)}`}</title></rect>;})}
          {['brut','cout_employeur'].map((key,i) => <g key={key} className={`mass-series-${i}`}><polyline points={rows.map((row,index)=>point(row,index,key)).join(' ')} fill="none" stroke="currentColor" strokeWidth="3"/>{rows.map((row,index)=>{const [cx,cy]=point(row,index,key).split(',');return <circle key={row.periode} cx={cx} cy={cy} r="5" fill="currentColor" tabIndex="0"><title>{`${periodLabel(row.periode)} : ${key} ${money(Number(row[`${key}_valide`])+Number(row[`${key}_paye`]))}`}</title></circle>;})}</g>)}
          {rows.filter((_,i)=>i===0 || i===rows.length-1).map(row=><text key={row.periode} x={row===rows[0]?50:600} y="225">{row.periode}</text>)}
        </svg><p className="mass-note"><span className="mass-series-0">● Brut</span> · <span className="mass-series-1">◆ Coût employeur</span> · XOF</p></div>}
      </MassPanel>
      <MassPanel title="Répartition du coût employeur" description="Par département · montants validés et payés">
        {!total ? <p className="leave-state">Aucun coût disponible.</p> : <><svg className="mass-donut" viewBox="0 0 160 160" role="img" aria-label="Répartition des coûts par département">{segments.map((row,i)=>{const fraction=row.value/total*100;const start=offset;offset+=fraction;return <circle key={row.label} cx="80" cy="80" r="58" pathLength="100" fill="none" strokeWidth="22" className={`mass-segment-${i}`} strokeDasharray={`${fraction} ${100-fraction}`} strokeDashoffset={-start} transform="rotate(-90 80 80)"><title>{`${row.label} : ${money(row.value)} (${fraction.toFixed(1)} %)`}</title></circle>;})}</svg><ul className="mass-donut-legend">{segments.map((row,i)=><li key={row.label}><span className={`mass-series-${i}`}>{i+1}. {row.label}</span> : {money(row.value)} · {(row.value/total*100).toFixed(1)} %</li>)}</ul></>}
      </MassPanel>
    </div>
    {report.disponibilite?.note ? <p className="mass-note">{report.disponibilite.note}</p> : null}
  </>;
}
