import React, { useEffect, useState } from 'react';
import { navigate } from '../../../shared/lib/navigation.js';
import { clearSession, getUser, hasPermission } from '../../../shared/lib/api.js';
import MyTimesheets from '../components/MyTimesheets.jsx';
import ReviewTimesheets from '../components/ReviewTimesheets.jsx';
import TimesheetProjects from '../components/TimesheetProjects.jsx';
import TimesheetCosts from '../components/TimesheetCosts.jsx';

export default function TimesheetsPage() {
  const [user] = useState(getUser);
  const valid = Boolean(localStorage.getItem('access_token')) && Array.isArray(user?.permissions);
  useEffect(() => {
    if (valid) return;
    clearSession(); navigate('/connexion?session=permissions', { replace: true });
  }, [valid]);
  return valid ? <TimesheetWorkspace /> : null;
}

function TimesheetWorkspace() {
  const [tab, setTab] = useState('mine');
  const tabs = [
    { id: 'mine', label: 'Mes feuilles', visible: true },
    { id: 'review', label: 'À valider', visible: hasPermission('feuille_temps.decide') },
    { id: 'projects', label: 'Projets et affectations', visible: hasPermission('projet.read') },
    { id: 'costs', label: 'Rapprochement des coûts', visible: hasPermission('paie.read') },
  ];
  return <><div className="timesheet-workspace">
    <section className="page-heading"><div><h1>Feuilles de temps</h1>
      <p className="page-description">Déclarez votre temps par projet et tâche. Les heures validées par le manager alimentent les coûts du module TGM.</p></div></section>
    <nav className="timesheet-tabs" aria-label="Espaces des feuilles de temps">{tabs.filter((item) => item.visible).map((item) => <button key={item.id} type="button" aria-current={tab === item.id ? 'page' : undefined}
      className={tab === item.id ? 'timesheet-tab active' : 'timesheet-tab'} onClick={() => setTab(item.id)}>{item.label}</button>)}</nav>
    {tab === 'mine' && <MyTimesheets />}
    {tab === 'review' && hasPermission('feuille_temps.decide') && <ReviewTimesheets />}
    {tab === 'projects' && hasPermission('projet.read') && <TimesheetProjects />}
    {tab === 'costs' && hasPermission('paie.read') && <TimesheetCosts />}
  </div></>;
}
