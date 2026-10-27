import React from 'react';
import { actionLabels, availableActions, employeeName, money, payrollStatuses } from '../lib/payroll.js';

/** @param {{ payrolls: Array, permissions: Object, busy: boolean, onDetail: Function, onAction: Function }} props */
export default function PayrollList({ payrolls, permissions, busy, onDetail, onAction }) {
  if (!payrolls.length) return <p className="leave-state">Aucune paie ne correspond aux filtres.</p>;
  return <div className="leave-request-list">{payrolls.map((payroll) => <article key={payroll.id} className="leave-request-card payroll-card">
    <div className="leave-request-main">
      <span className={`leave-status payroll-status-${payroll.statut.toLowerCase()}`}>{payrollStatuses[payroll.statut] || payroll.statut}</span>
      <h3>{employeeName(payroll)} · {payroll.periode}</h3>
      <p>{payroll.libelle} · Matricule : {payroll.employe_matricule || 'Non renseigné'}</p>
      <p>Brut : {money(payroll.salaire_brut, payroll.devise)} · Net : {money(payroll.salaire_net, payroll.devise)}</p>
      {!payroll.bulletin_disponible && !payroll.bulletin_generable && ['VALIDEE', 'PAYE'].includes(payroll.statut) && <p>Bulletin indisponible : historique de calcul incomplet.</p>}
    </div>
    <div className="leave-request-actions">
      <button type="button" className="outline-button" onClick={() => onDetail(payroll.id)} disabled={busy}>Voir le détail</button>
      {availableActions(payroll, permissions).map((action) => <button key={action} type="button"
        className={action === 'delete' || action === 'cancel' ? 'danger-button' : 'outline-button'}
        onClick={() => onAction(action, payroll)} disabled={busy}>{actionLabels[action]}</button>)}
    </div>
  </article>)}</div>;
}
