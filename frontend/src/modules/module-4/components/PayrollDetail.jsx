import React, { useEffect, useState } from 'react';
import { apiRequest, formatApiError } from '../../../shared/lib/api.js';
import PayrollDialog from './PayrollDialog.jsx';
import { dateTime, employeeName, money, payrollPath, payrollStatuses } from '../lib/payroll.js';

/** @param {{ payrollId: number | string, onClose: Function }} props */
export default function PayrollDetail({ payrollId, onClose }) {
  const [state, setState] = useState({ loading: true, detail: null, error: '' });
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    setState({ loading: true, detail: null, error: '' });
    apiRequest(`${payrollPath}${payrollId}/`).then(
      (detail) => { if (active) setState({ loading: false, detail, error: '' }); },
      (error) => { if (active) setState({ loading: false, detail: null, error: formatApiError(error.details || error.message) }); },
    );
    return () => { active = false; };
  }, [payrollId, attempt]);
  return <PayrollDialog title={`Détail de la paie #${payrollId}`} onClose={onClose}>
    {state.loading && <p role="status">Chargement du détail…</p>}
    {state.error && <div role="alert"><p>{state.error}</p><button type="button" className="outline-button" onClick={() => setAttempt((value) => value + 1)}>Réessayer</button></div>}
    {state.detail && <PayrollInformation payroll={state.detail} />}
    <div className="form-footer"><button type="button" className="outline-button" onClick={onClose} autoFocus>Fermer</button></div>
  </PayrollDialog>;
}

/** @param {{ payroll: Object }} props */
export function PayrollInformation({ payroll }) {
  const detail = payroll.detail_calcul || {};
  const cash = (value) => money(value, payroll.devise);
  const fields = [
    ['Employé', employeeName(payroll)], ['Matricule', payroll.employe_matricule || 'Non renseigné'],
    ['Période', payroll.periode], ['Libellé', payroll.libelle], ['Statut', payrollStatuses[payroll.statut] || payroll.statut],
    ['Base calculée', cash(payroll.salaire_base)], ['Salaire brut', cash(payroll.salaire_brut)],
    ['Salaire net', cash(payroll.salaire_net)], ['Coût employeur', cash(payroll.cout_charge)],
    ['Cotisations totales', cash(payroll.cotisations)], ['Date de calcul', dateTime(payroll.date_calcul)],
    ['Date de validation', dateTime(payroll.date_validation)], ['Date de paiement', dateTime(payroll.date_paiement)],
    ['Date d’annulation', dateTime(payroll.date_annulation)], ['Motif d’annulation', payroll.motif_annulation || 'Aucun'],
  ];
  return <>
    <dl className="leave-detail-fields payroll-detail-grid">{fields.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>
    {detail.regle ? <>
      <h3>Profil appliqué</h3>
      <p>{detail.regle.code} · {detail.regle.source_reference || 'Aucune référence renseignée'}</p>
    </> : <p>Aucun historique de calcul disponible pour cette paie.</p>}
    {detail.contrat && <><h3>Contrat et absences</h3><p>{detail.contrat.jours_payes} jours payés sur {detail.contrat.jours_ouvres_mois} jours ouvrés · {detail.contrat.jours_absence_payee} jours d’absence payée · {detail.contrat.jours_absence_non_payee} jours d’absence non payée.</p></>}
    {detail.cotisations && <><h3>Retenues et charges</h3><dl className="leave-detail-fields payroll-detail-grid">
      <div><dt>CNSS salariale</dt><dd>{cash(detail.cotisations.cnss_salariale)}</dd></div>
      <div><dt>CNSS patronale</dt><dd>{cash(detail.cotisations.cnss_patronale)}</dd></div>
      <div><dt>TPA patronale</dt><dd>{cash(detail.cotisations.tpa_patronale)}</dd></div>
      <div><dt>IUTS net</dt><dd>{cash(detail.iuts?.net)}</dd></div>
    </dl></>}
    {detail.elements?.length > 0 && <><h3>Éléments inclus dans le calcul</h3><ul>{detail.elements.map((element, index) => <li key={element.id || index}>{element.libelle} · {cash(element.montant)}</li>)}</ul></>}
    {detail.hypotheses?.length > 0 && <><h3>Hypothèses du calcul</h3><ul>{detail.hypotheses.map((value) => <li key={value}>{value}</li>)}</ul></>}
  </>;
}
