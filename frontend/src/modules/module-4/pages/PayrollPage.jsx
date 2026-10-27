import React, { useEffect, useState } from 'react';
import { navigate } from '../../../shared/lib/navigation.js';
import FormField from '../../../shared/components/FormField.jsx';
import { clearSession, getUser, hasPermission } from '../../../shared/lib/api.js';
import PayrollAction from '../components/PayrollAction.jsx';
import PayrollDetail from '../components/PayrollDetail.jsx';
import PayrollEditor from '../components/PayrollEditor.jsx';
import PayrollList from '../components/PayrollList.jsx';
import PayrollRuleManager from '../components/PayrollRuleManager.jsx';
import TransferOrders from '../components/TransferOrders.jsx';
import usePayrollData from '../hooks/usePayrollData.js';
import usePayrollActions from '../hooks/usePayrollActions.js';
import { employeeName, payrollStatuses } from '../lib/payroll.js';

export default function PayrollPage() {
  const [user] = useState(getUser);
  const sessionValid = Boolean(localStorage.getItem('access_token')) && Array.isArray(user?.permissions);
  useEffect(() => {
    if (sessionValid) return;
    clearSession(); navigate('/connexion?session=permissions', { replace: true });
  }, [sessionValid]);
  return sessionValid ? <PayrollWorkspace /> : null;
}

function PayrollWorkspace() {
  const permissions = {
    read: hasPermission('paie.read'), create: hasPermission('paie.create'),
    update: hasPermission('paie.update'), delete: hasPermission('paie.delete'),
    employees: hasPermission('employe.read'),
    ordersRead: hasPermission('ordre_virement.read'),
  };
  const transferPermissions = { read: permissions.ordersRead, create: hasPermission('ordre_virement.create'),
    update: hasPermission('ordre_virement.update'), delete: hasPermission('ordre_virement.delete'),
    payrollRead: permissions.read, payrollUpdate: permissions.update,
    document: permissions.read && permissions.ordersRead && hasPermission('ordre_virement.generate_document') };
  const data = usePayrollData({ read: permissions.read, employees: permissions.employees && (permissions.create || permissions.update), rules: permissions.read, orders: permissions.ordersRead });
  const { mutation, editor, notice, downloadError, downloading, busy, openAction, saved, closeEditor } = usePayrollActions(data.load);
  const [filters, setFilters] = useState({ period: '', status: '', search: '' });
  const [detailId, setDetailId] = useState(null);
  const [section, setSection] = useState(permissions.read ? 'payrolls' : 'orders');
  const changeFilter = (key) => (event) => setFilters((value) => ({ ...value, [key]: event.target.value }));
  const filtered = data.payrolls.filter((payroll) => (!filters.period || payroll.periode === filters.period)
    && (!filters.status || payroll.statut === filters.status)
    && `${employeeName(payroll)} ${payroll.employe_matricule || ''} ${payroll.libelle}`.toLocaleLowerCase('fr').includes(filters.search.trim().toLocaleLowerCase('fr')));
  const canChooseEmployee = permissions.employees && !data.errors.employees && data.employees.length > 0;
  return <>
    <section className="page-heading"><div>
      <h1>Gestion des paies</h1><p className="page-description">Préparez les paies, consultez les calculs et gérez les bulletins.</p>
    </div>{section === 'payrolls' && permissions.read && permissions.create && <button type="button" className="primary-button" disabled={busy || data.loading || !canChooseEmployee} onClick={() => openAction('create')}>Nouvelle paie</button>}</section>
    {!permissions.read && !permissions.ordersRead ? <p className="message-box error" role="alert">Votre compte ne possède aucune permission de consultation des paies ou des ordres.</p> : <>
      <nav className="module-tabs" aria-label="Sections de la paie">
        {permissions.read && <button type="button" className={section === 'payrolls' ? 'active' : ''} aria-pressed={section === 'payrolls'} onClick={() => setSection('payrolls')}>Paies</button>}
        {permissions.read && <button type="button" className={section === 'rules' ? 'active' : ''} aria-pressed={section === 'rules'} onClick={() => setSection('rules')}>Règles de paie</button>}
        {permissions.ordersRead && <button type="button" className={section === 'orders' ? 'active' : ''} aria-pressed={section === 'orders'} onClick={() => setSection('orders')}>Ordres de virement</button>}
      </nav>
      {section === 'orders' ? <TransferOrders orders={data.orders} payrolls={data.payrolls} loading={data.loading} error={data.errors.orders || ''} payrollError={data.errors.payrolls || ''} permissions={transferPermissions} onChanged={data.load} />
        : section === 'rules' ? <PayrollRuleManager rules={data.rules} loading={data.loading} error={data.errors.rules || ''} permissions={permissions} onChanged={data.load} /> : <>
      {permissions.create && !permissions.employees && <p className="message-box">La création nécessite aussi la permission de consulter les employés.</p>}
      {data.errors.employees && <p className="message-box error" role="alert">Liste des employés : {data.errors.employees}</p>}
      {permissions.create && permissions.employees && !data.loading && !data.errors.employees && !data.employees.length && <p className="message-box">Aucun employé disponible pour créer une paie.</p>}
      {notice && <p className="message-box" role="status">{notice}</p>}
      {downloadError && <p className="message-box error" role="alert">{downloadError}</p>}
      {downloading && <p role="status">Téléchargement du bulletin…</p>}
      <section className="content-card">
        <div className="card-heading"><h2>Paies des employés</h2><button type="button" className="outline-button" disabled={busy || data.loading} onClick={data.load}>Actualiser</button></div>
        <div className="payroll-filters form-grid">
          <FormField label="Période">{(a11y) => <input {...a11y} type="month" value={filters.period} onChange={changeFilter('period')} />}</FormField>
          <FormField label="Statut">{(a11y) => <select {...a11y} value={filters.status} onChange={changeFilter('status')}><option value="">Tous les statuts</option>{Object.entries(payrollStatuses).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select>}</FormField>
          <FormField label="Rechercher un employé ou un libellé">{(a11y) => <input {...a11y} type="search" value={filters.search} onChange={changeFilter('search')} />}</FormField>
          <button type="button" className="outline-button" onClick={() => setFilters({ period: '', status: '', search: '' })}>Réinitialiser les filtres</button>
        </div>
        {data.loading ? <p className="leave-state" role="status">Chargement des paies…</p> : data.errors.payrolls
          ? <p className="message-box error" role="alert">{data.errors.payrolls}</p>
          : <PayrollList payrolls={filtered} permissions={permissions} busy={busy} onDetail={setDetailId} onAction={openAction} />}
      </section>
      </>}
    </>}
    {detailId !== null && <PayrollDetail payrollId={detailId} onClose={() => setDetailId(null)} />}
    {editor && (['create', 'edit'].includes(editor.action)
      ? <PayrollEditor payroll={editor.payroll} employees={data.employees} canChooseEmployee={Boolean(canChooseEmployee)} mutation={mutation} onClose={closeEditor} onSaved={saved} />
      : <PayrollAction action={editor.action} payroll={editor.payroll} rules={data.rules} rulesError={data.errors.rules || ''} mutation={mutation} onClose={closeEditor} onSaved={saved} />)}
  </>;
}
