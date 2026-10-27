import React, { useEffect, useState } from 'react';
import { apiRequest, formatApiError } from '../../../shared/lib/api.js';
import PayrollDialog from './PayrollDialog.jsx';
import { dateTime, employeeName } from '../lib/payroll.js';
import { transfersPath, transferStatuses } from '../lib/transfers.js';

/** @param {{ orderId: number | string, onClose: Function }} props */
export default function TransferDetail({ orderId, onClose }) {
  const [state, setState] = useState({ loading: true, detail: null, error: '' });
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    setState({ loading: true, detail: null, error: '' });
    apiRequest(`${transfersPath}${orderId}/`).then(
      (detail) => { if (active) setState({ loading: false, detail, error: '' }); },
      (error) => { if (active) setState({ loading: false, detail: null, error: formatApiError(error.details || error.message) }); },
    );
    return () => { active = false; };
  }, [orderId, attempt]);
  return <PayrollDialog title={`Détail de l’ordre #${orderId}`} onClose={onClose}>
    {state.loading && <p role="status">Chargement du détail…</p>}
    {state.error && <div role="alert"><p>{state.error}</p><button type="button" className="outline-button" onClick={() => setAttempt((value) => value + 1)}>Réessayer</button></div>}
    {state.detail && <TransferInformation order={state.detail} />}
    <div className="form-footer"><button type="button" className="outline-button" onClick={onClose} autoFocus>Fermer</button></div>
  </PayrollDialog>;
}

export function TransferInformation({ order }) {
  const fields = [
    ['Employé', employeeName(order)], ['Matricule', order.employe_matricule || 'Non renseigné'],
    ['Période', order.periode], ['Statut', transferStatuses[order.statut] || order.statut],
    ['Date de génération', dateTime(order.date_generation)], ['Date de traitement', dateTime(order.date_traitement)],
    ['Décision prise par', [order.decideur_prenom, order.decideur_nom].filter(Boolean).join(' ') || 'Non renseigné'],
    ['Date de décision', dateTime(order.date_decision)], ['Motif ou commentaire', order.motif_decision || 'Non renseigné'],
  ];
  return <dl className="leave-detail-fields payroll-detail-grid">{fields.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>;
}
