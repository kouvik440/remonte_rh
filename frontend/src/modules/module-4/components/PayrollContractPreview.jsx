import React from 'react';
import usePayrollContract from '../hooks/usePayrollContract.js';
import { money } from '../lib/payroll.js';

const statuses = { EN_COURS: 'En cours', CLOS: 'Clos', RESILIE: 'Résilié' };

/** @param {{ employeeId: number | string, period: string }} props */
export default function PayrollContractPreview({ employeeId, period }) {
  const state = usePayrollContract(employeeId, period);
  return <section className="payroll-contract-preview" aria-label="Contrat pour la période de paie" aria-live="polite">
    <h3>Contrat pour la période de paie</h3>
    {!state.ready ? <p>Choisissez un employé et une période pour consulter son contrat.</p>
      : state.loading ? <p role="status">Chargement du contrat…</p>
        : state.error ? <div role="alert"><p>{state.error}</p><button type="button" className="outline-button" onClick={state.retry}>Réessayer</button></div>
          : state.context && <PayrollContractInformation context={state.context} />}
  </section>;
}

/** @param {{ context: Object }} props */
export function PayrollContractInformation({ context }) {
  return <>
    {context.state === 'MISSING' && <p className="message-box">Aucun contrat ne couvre cette période. Ajoutez ou corrigez le contrat dans le module Employés avant de calculer la paie.</p>}
    {context.state === 'AMBIGUOUS' && <p className="message-box error" role="alert">Plusieurs contrats couvrent cette période. Corrigez leurs dates dans le module Employés : le calcul ne peut pas choisir entre eux.</p>}
    {context.contracts.map((contract) => <dl key={contract.id} className="leave-detail-fields payroll-detail-grid">
      <div><dt>Types de contrat</dt><dd>{contract.types_libelles?.join(', ') || 'Non renseignés'}</dd></div>
      <div><dt>Salaire mensuel contractuel</dt><dd>{money(contract.salaire_base, 'XOF')}</dd></div>
      <div><dt>Heures journalières</dt><dd>{contract.heures_journalieres ? `${contract.heures_journalieres} h/jour` : 'Non renseignées'}</dd></div>
      <div><dt>Statut du contrat</dt><dd>{statuses[contract.statut] || contract.statut}</dd></div>
      <div><dt>Date de début</dt><dd>{contract.date_debut}</dd></div>
      <div><dt>Date de fin</dt><dd>{contract.date_fin || 'Sans date de fin renseignée'}</dd></div>
    </dl>)}
    {context.state === 'READY' && <p>Ces informations sont reprises du contrat. Le calcul appliquera le prorata, les absences et les éléments variables ; le net sera disponible après calcul.</p>}
  </>;
}
