import React from 'react';

/** @param {{ balances: Array, year: number, onYearChange: Function, loading: boolean }} props */
export default function LeaveBalanceManager({ balances, year, onYearChange, loading }) {
  return <section className="content-card leave-management">
    <div className="card-heading"><h2>Soldes de congé</h2><div className="month-controls">
      <button type="button" className="outline-button" disabled={year <= 1 || loading} onClick={() => onYearChange(year - 1)} aria-label="Année précédente">←</button>
      <strong>{year}</strong>
      <button type="button" className="outline-button" disabled={year >= 9999 || loading} onClick={() => onYearChange(year + 1)} aria-label="Année suivante">→</button>
    </div></div>
    <p>Le droit annuel est défini dans chaque type de congé et s'applique à tous les employés. Les jours pris, en attente et disponibles sont calculés automatiquement.</p>
    {loading ? <p role="status">Chargement des soldes…</p> : balances.length === 0 ? <p>Aucun solde enregistré pour cette année.</p> : <div className="leave-balance-grid">{balances.map((balance) => <article className="leave-balance-card" key={`${balance.employe}-${balance.type_conge}`}>
      <h3>{balance.employe_prenom} {balance.employe_nom}</h3><p>{balance.employe_matricule} · {balance.type_conge_libelle} · {balance.annee}</p>
      <dl className="balance-numbers">{[['Disponibles', balance.disponible], ['En attente', balance.en_attente], ['Pris', balance.pris], ['Acquis', balance.acquis]].map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>
      {balance.disponible < 0 && <p role="status">Quota dépassé : vérifier les demandes existantes.</p>}

    </article>)}</div>}
  </section>;
}
