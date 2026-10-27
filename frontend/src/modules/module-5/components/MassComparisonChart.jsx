import React from 'react';
import { money, periodLabel } from '../lib/payrollMass.js';

/** @param {{ rows: Array, metric: { title: string, validatedKey: string, paidKey: string } }} props */
export default function MassComparisonChart({ rows, metric }) {
  const maximum = rows.reduce((largest, row) => Math.max(largest, Number(row[metric.validatedKey]), Number(row[metric.paidKey])), 1);
  const width = Math.max(620, rows.length * 130 + 160);
  return <figure className="mass-comparison">
    <figcaption>{metric.title} · XOF</figcaption>
    <div className="mass-chart" role="region" aria-label={`Graphique : ${metric.title}, valeurs dans le tableau suivant`} tabIndex="0">
      <svg viewBox={`0 0 ${width} 235`} width={width} height="235" role="img" aria-label={`${metric.title} : comparaison des paies validées et payées par période`}>
        {[0, 1, 2, 3].map((step) => {
          const y = 180 - step * 50;
          return <g key={step}>
            <line className="mass-chart-grid" x1="125" x2={width - 10} y1={y} y2={y} />
            <text x="115" y={y + 4} textAnchor="end">{money(maximum * step / 3)}</text>
          </g>;
        })}
        {rows.map((row, index) => <PeriodBars key={row.periode || row.annee} row={row} index={index} metric={metric} maximum={maximum} />)}
      </svg>
    </div>
  </figure>;
}

function PeriodBars({ row, index, metric, maximum }) {
  const period = row.periode || row.annee;
  const validated = Number(row[metric.validatedKey]) / maximum * 150;
  const paid = Number(row[metric.paidKey]) / maximum * 150;
  const center = index * 130 + 185;
  return <g>
    <title>{`${periodLabel(period)} : ${metric.title}, validé ${money(row[metric.validatedKey])}, payé ${money(row[metric.paidKey])}`}</title>
    <rect className="mass-bar-validated" x={center - 32} y={180 - validated} width="28" height={validated} />
    <rect className="mass-bar-paid" x={center + 4} y={180 - paid} width="28" height={paid} />
    <text x={center} y="210" textAnchor="middle">{period}</text>
  </g>;
}
