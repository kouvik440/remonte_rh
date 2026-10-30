import React, { useEffect, useState } from 'react';
import { navigate } from '../../../shared/lib/navigation.js';
import { clearSession, getUser, hasPermission } from '../../../shared/lib/api.js';
import useTgmReport from '../hooks/useTgmReport.js';
import { initialPeriod, reportPaths } from '../lib/tgm.js';
import TgmFilters from '../components/TgmFilters.jsx';
import TgmEmployees from '../components/TgmEmployees.jsx';
import TgmProjectCosts from '../components/TgmProjectCosts.jsx';
import TgmOverview from '../components/TgmOverview.jsx';
import TgmProductiveSimulation from '../components/TgmProductiveSimulation.jsx';
import TgmSimulation from '../components/TgmSimulation.jsx';

export default function TgmPage() {
  const [user] = useState(getUser);
  const sessionValid = Boolean(localStorage.getItem('access_token')) && Array.isArray(user?.permissions);
  useEffect(() => {
    if (sessionValid) return;
    clearSession(); navigate('/connexion?session=permissions', { replace: true });
  }, [sessionValid]);
  return sessionValid ? <TgmWorkspace /> : null;
}

function ReportState({ data, label, children }) {
  if (data.loading) return <p className="leave-state" role="status">Chargement {label}…</p>;
  if (data.error) return <div className="message-box error" role="alert">{data.error} <button className="outline-button" type="button" onClick={data.reload}>Réessayer {label}</button></div>;
  return data.report ? children(data.report) : null;
}

function TgmWorkspace() {
  const canRead = hasPermission('paie.read');
  const [period, setPeriod] = useState(initialPeriod);
  const paths = reportPaths(period);
  const rates = useTgmReport(paths.rates, canRead);
  const costs = useTgmReport(paths.costs, canRead);
  function apply(nextPeriod) {
    if (nextPeriod.start === period.start && nextPeriod.end === period.end && nextPeriod.department === period.department && nextPeriod.employee === period.employee) {
      rates.reload(); costs.reload();
    } else setPeriod(nextPeriod);
  }
  return <><div className="tgm-workspace">
    <section className="page-heading"><div><h1>Taux journalier et horaire moyen</h1>
      <p className="page-description">Consultez le coût de chaque employé et les coûts imputables aux projets à partir des heures validées.</p>
    </div></section>
    {!canRead ? <p className="message-box error" role="alert">La permission paie.read est nécessaire pour consulter les taux et coûts projets.</p> : <>
      <TgmFilters applied={period} busy={rates.loading || costs.loading} onApply={apply} employees={rates.report?.employes} />
      <ReportState data={rates} label="des taux">{(report) => <><TgmOverview report={report} /><TgmEmployees report={report} /><TgmProductiveSimulation key={`${period.start}-${period.end}`} period={period} employees={report.employes} /></>}</ReportState>
      <ReportState data={costs} label="des coûts projets">{(report) => <>
        <TgmProjectCosts report={report} />
        <TgmSimulation key={`${period.start}-${period.end}`} projects={report.projets} period={period} />
      </>}</ReportState>
    </>}
  </div></>;
}
