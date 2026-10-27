import React, { useEffect, useState } from 'react';
import { navigate } from '../../../shared/lib/navigation.js';
import { clearSession, getUser, hasPermission } from '../../../shared/lib/api.js';
import MassFilters from '../components/MassFilters.jsx';
import MassTotals from '../components/MassTotals.jsx';
import MassEvolution from '../components/MassEvolution.jsx';
import MassBreakdown from '../components/MassBreakdown.jsx';
import MassPanel from '../components/MassPanel.jsx';
import usePayrollMass from '../hooks/usePayrollMass.js';
import useMassExport from '../hooks/useMassExport.js';
import { initialFilters, periodLabel } from '../lib/payrollMass.js';

export default function PayrollMassPage() {
  const [user] = useState(getUser);
  const sessionValid = Boolean(localStorage.getItem('access_token')) && Array.isArray(user?.permissions);
  useEffect(() => {
    if (sessionValid) return;
    clearSession(); navigate('/connexion?session=permissions', { replace: true });
  }, [sessionValid]);
  return sessionValid ? <MassWorkspace /> : null;
}

function MassWorkspace() {
  const canRead = hasPermission('paie.read');
  const canReadDepartments = hasPermission('departement.read');
  const [filters, setFilters] = useState(initialFilters);
  const data = usePayrollMass(filters, canRead, canReadDepartments);
  const exports = useMassExport(filters);
  const busy = data.loading || Boolean(exports.downloading);
  return <>
    <div className="mass-workspace">
    <section className="page-heading"><div><h1>Masse salariale</h1>
      <p className="page-description">Suivez les salaires et le coût employeur par période, département et type de contrat.</p></div></section>
    {!canRead ? <p className="message-box error" role="alert">La permission paie.read est nécessaire pour consulter la masse salariale.</p> : <>
      <MassFilters applied={filters} departments={data.departments} canReadDepartments={canReadDepartments} departmentError={data.departmentError} busy={busy} onApply={setFilters} />
      {data.loading ? <p className="leave-state" role="status">Chargement de l’analyse…</p> : data.error ? <div className="message-box error" role="alert">{data.error} <button type="button" className="outline-button" onClick={data.reload}>Réessayer</button></div> : data.report && <>
        <MassPanel title={`De ${periodLabel(filters.start)} à ${periodLabel(filters.end)}`}
          description={`${filters.department ? data.departments.find((item) => String(item.id) === filters.department)?.nom || 'Département sélectionné' : 'Tous les départements'} · Devise : XOF`}
          actions={<div className="mass-exports" aria-label="Exporter l’analyse" aria-busy={Boolean(exports.downloading)}>
            {['csv', 'xlsx', 'pdf'].map((format) => <button key={format} type="button" className="outline-button" disabled={busy} onClick={() => exports.download(format)}>Exporter {format === 'xlsx' ? 'Excel' : format.toUpperCase()}</button>)}
            <button type="button" className="outline-button" disabled={busy} onClick={data.reload}>Actualiser</button>
          </div>}>
          <p className="mass-note">Seules les paies validées et payées sont incluses. Une paie payée apparaît uniquement dans les montants payés. Les brouillons, calculées et annulées sont exclus.</p>
          <p className="mass-note">Les exports reprennent cette période, ce département et l’évolution {filters.granularity === 'annuelle' ? 'annuelle' : 'mensuelle'} sélectionnée.</p>
        </MassPanel>
        {exports.downloading && <p role="status">Téléchargement de l’export…</p>}
        {exports.error && <p className="message-box error" role="alert">{exports.error}</p>}
        {!data.report.totaux.paies_validees && !data.report.totaux.paies_payees && <p className="message-box" role="status">Aucune paie validée ou payée sur ce périmètre.</p>}
        <MassTotals totals={data.report.totaux} />
        <MassEvolution data={data.evolution} />
        <MassBreakdown title="Par département" rows={data.report.par_departement} labelKey="departement" idKey="departement_id" />
        <MassBreakdown title="Par type de contrat" rows={data.report.par_type_contrat} labelKey="type_contrat" idKey="type_contrat_id" note={data.report.note_ventilation_contrat} />
      </>}
    </>}
    </div>
  </>;
}
