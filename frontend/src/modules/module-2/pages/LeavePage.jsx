import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { navigate } from '../../../shared/lib/navigation.js';
import LeaveActionConfirmation from '../components/LeaveActionConfirmation.jsx';
import LeaveTypeManager from '../components/LeaveTypeManager.jsx';
import LeaveBalanceManager from '../components/LeaveBalanceManager.jsx';
import LeavePlanning from '../components/LeavePlanning.jsx';
import LeaveRequestDetail from '../components/LeaveRequestDetail.jsx';
import { dateKey, firstDayOfMonth, lastDayOfMonth } from '../lib/calendar.js';
import { apiRequest, clearSession, formatApiError, getUser, hasPermission } from '../../../shared/lib/api.js';

const humanDate = (value) => new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(`${value}T12:00:00`));

const blankRequest = () => ({ type_conge: '', date_debut: '', date_fin: '', motif: '' });

const requestFieldLabels = {
  type_conge: 'Type de congé',
  date_debut: 'Date de début',
  date_fin: 'Date de fin',
  motif: 'Motif',
};

const getRequestFieldErrors = (details) => {
  if (!details || typeof details !== 'object' || Array.isArray(details)) return {};
  return Object.fromEntries(
    Object.entries(details)
      .filter(([field]) => Object.hasOwn(requestFieldLabels, field))
      .map(([field, value]) => [field, (Array.isArray(value) ? value : [value]).map(String).join(' ')])
  );
};

export default function LeavePage() {
  const user = useMemo(() => getUser(), []);
  const [activeTab, setActiveTab] = useState(() => hasPermission('demande_absence.read')
    ? 'requests'
    : hasPermission('solde_conge.read')
      ? 'balances'
      : 'types');
  const [requests, setRequests] = useState([]);
  const [pendingAction, setPendingAction] = useState(null);
  const [actionBusy, setActionBusy] = useState(false);
  const actionLock = useRef(false);
  const [detailRequestId, setDetailRequestId] = useState(null);
  const [types, setTypes] = useState([]);
  const [balances, setBalances] = useState([]);
  const [events, setEvents] = useState([]);
  const [planningLoading, setPlanningLoading] = useState(true);
  const [planningError, setPlanningError] = useState('');
  const loadVersion = useRef(0);
  const [month, setMonth] = useState(() => firstDayOfMonth(new Date()));
  const [requestForm, setRequestForm] = useState(blankRequest);
  const [requestErrors, setRequestErrors] = useState({});
  const [formOpen, setFormOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [messageIsError, setMessageIsError] = useState(false);

  const canReadRequests = hasPermission('demande_absence.read');
  const canCreateRequest = hasPermission('demande_absence.create');
  const canDecide = hasPermission('demande_absence.update');
  const canReadTypes = hasPermission('conge.read');
  const canReadBalances = hasPermission('solde_conge.read');
  const canViewAll = canDecide;
  const monthStart = useMemo(() => dateKey(firstDayOfMonth(month)), [month]);
  const monthEnd = useMemo(() => dateKey(lastDayOfMonth(month)), [month]);
  const currentYear = month.getFullYear();

  const notify = useCallback((text, isError = false) => {
    setMessage(text);
    setMessageIsError(isError);
  }, []);

  const loadData = useCallback(async () => {
    const version = ++loadVersion.current;
    setLoading(true);
    setPlanningLoading(canReadRequests);
    setPlanningError('');
    const tasks = [];
    if (canReadRequests) {
      tasks.push({ key: 'demandes', promise: apiRequest('/api/demandes-absence/') });
      const query = new URLSearchParams({ date_debut: monthStart, date_fin: monthEnd });
      tasks.push({ key: 'planning', promise: apiRequest(`/api/planning/?${query}`) });
    }
    if (canReadTypes) tasks.push({ key: 'types', promise: apiRequest('/api/conges/types/') });
    if (canReadBalances) tasks.push({ key: 'soldes', promise: apiRequest(`/api/soldes-conge/?annee=${currentYear}`) });

    const results = await Promise.allSettled(tasks.map((task) => task.promise));
    if (version !== loadVersion.current) return;

    const failures = [];
    results.forEach((result, index) => {
      const { key } = tasks[index];
      if (result.status === 'fulfilled') {
        if (key === 'demandes') setRequests(result.value);
        if (key === 'planning') setEvents(result.value);
        if (key === 'types') setTypes(result.value);
        if (key === 'soldes') setBalances(result.value);
      } else {
        failures.push({ key, error: result.reason });
        if (key === 'planning') setEvents([]);
      }
    });

    const authFailure = failures.find(({ error }) => error.status === 401);
    if (authFailure) {
      const error = authFailure.error;
      if (error.status === 401) {
        clearSession();
        navigate('/connexion?session=expired', { replace: true });
      }
    } else if (failures.length > 0) {
      const planningFailure = failures.find(({ key }) => key === 'planning');
      if (planningFailure) {
        const errorMessage = formatApiError(planningFailure.error.details || planningFailure.error.message);
        setPlanningError(errorMessage);
        notify(`Impossible de charger le planning : ${errorMessage}`, true);
      } else {
        notify(`Chargement incomplet : ${formatApiError(failures[0].error.details || failures[0].error.message)}`, true);
      }
    }
    setPlanningLoading(false);
    setLoading(false);
  }, [canReadRequests, canReadTypes, canReadBalances, monthStart, monthEnd, currentYear, notify]);

  useEffect(() => {
    if (!localStorage.getItem('access_token')) {
      navigate('/connexion', { replace: true });
      return;
    }
    if (!Array.isArray(user?.permissions)) {
      clearSession();
      navigate('/connexion?session=permissions', { replace: true });
      return;
    }
    loadData();
  }, [user, loadData]);

  const sortedRequests = useMemo(() => [...requests].sort((a, b) => b.date_demande.localeCompare(a.date_demande)), [requests]);

  const submitRequest = async (event) => {
    event.preventDefault();
    if (saving || !canCreateRequest) return;
    setSaving(true);
    try {
      await apiRequest('/api/demandes-absence/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...requestForm, type_conge: Number(requestForm.type_conge) }),
      });
      setRequestForm(blankRequest());
      setRequestErrors({});
      setFormOpen(false);
      notify('Votre demande a été envoyée.');
      await loadData();
    } catch (error) {
      const fieldErrors = getRequestFieldErrors(error.details);
      setRequestErrors(fieldErrors);
      const hasFieldErrors = Object.keys(fieldErrors).length > 0;
      if (hasFieldErrors) {
        document.getElementById(Object.keys(fieldErrors)[0])?.focus();
      }
      notify(
        hasFieldErrors
          ? 'La demande n’a pas été enregistrée. Corrigez les erreurs indiquées dans le formulaire.'
          : `Envoi impossible : ${formatApiError(error.details || error.message)}`,
        true,
      );
    } finally {
      setSaving(false);
    }
  };

  const confirmRequestAction = async () => {
    if (!pendingAction || actionLock.current) return;
    const { request, action } = pendingAction;
    if (request.statut !== 'EN_ATTENTE') return;
    const isDelete = action === 'supprimer';
    if (isDelete ? !(canDecide || String(request.employe) === String(user.id)) : !canDecide) return;
    actionLock.current = true;
    setActionBusy(true);
    try {
      const path = isDelete
        ? `/api/demandes-absence/${request.id}/`
        : `/api/demandes-absence/${request.id}/${action}/`;
      await apiRequest(path, { method: isDelete ? 'DELETE' : 'POST' });
      setPendingAction(null);
      notify(isDelete ? 'La demande a été supprimée.' : `Demande ${action === 'valider' ? 'validée' : 'refusée'}.`);
      await loadData();
    } catch (error) {
      setPendingAction(null);
      notify(`Action impossible : ${formatApiError(error.details || error.message)}`, true);
    } finally {
      actionLock.current = false;
      setActionBusy(false);
    }
  };

  const employeeLabel = (request) => [request.employe_prenom, request.employe_nom]
    .filter((name) => name?.trim()).join(' ') || 'Nom non renseigné';

  if (!localStorage.getItem('access_token')) return null;

  return (
    <>
        {pendingAction && (
          <LeaveActionConfirmation
            action={pendingAction.action}
            request={pendingAction.request}
            busy={actionBusy}
            onCancel={() => setPendingAction(null)}
            onConfirm={confirmRequestAction}
          />
        )}
        {detailRequestId !== null && canReadRequests && (
          <LeaveRequestDetail key={detailRequestId} requestId={detailRequestId} onClose={() => setDetailRequestId(null)} />
        )}
        <section className="page-heading">
          <div>
            <h1>Congés et absences</h1>
            <p className="page-description">Suivez vos demandes, vos droits et les absences de l’équipe.</p>
          </div>
          {canCreateRequest && <button type="button" className="primary-button" onClick={() => { setRequestErrors({}); setFormOpen((open) => !open); }}><span>＋</span> Nouvelle demande</button>}
        </section>

        {message && <div className={`message-box ${messageIsError ? 'error' : 'success'}`} role={messageIsError ? 'alert' : 'status'}>{message}</div>}

        {!canReadRequests && !canReadTypes && !canReadBalances && <div className="message-box error" role="alert">Votre compte ne possède pas de permission de consultation pour ce module.</div>}

        <nav className="module-tabs" aria-label="Sections congés et absences">
          {canReadRequests && <button type="button" className={activeTab === 'requests' ? 'active' : ''} onClick={() => setActiveTab('requests')}>Demandes</button>}
          {canReadRequests && <button type="button" className={activeTab === 'planning' ? 'active' : ''} onClick={() => setActiveTab('planning')}>Planning d’équipe</button>}
          {canReadBalances && <button type="button" className={activeTab === 'balances' ? 'active' : ''} onClick={() => setActiveTab('balances')}>Soldes</button>}
          {canReadTypes && <button type="button" className={activeTab === 'types' ? 'active' : ''} onClick={() => setActiveTab('types')}>Types de congé</button>}
        </nav>

        {formOpen && canCreateRequest && (
          <section className="content-card leave-form-card" aria-labelledby="leaveFormTitle">
            <div className="card-heading"><div><h2 id="leaveFormTitle">Nouvelle demande d’absence</h2><p>Les demandes sont envoyées au statut « En attente ».</p></div><button type="button" className="icon-button" onClick={() => setFormOpen(false)} aria-label="Fermer le formulaire">×</button></div>
            <form className="employee-form" onSubmit={submitRequest}>
              <fieldset className="leave-form-grid" disabled={saving}>
                <label className="form-field">Type de congé<select id="type_conge" aria-invalid={Boolean(requestErrors.type_conge)} aria-describedby={requestErrors.type_conge ? 'type_conge-error' : undefined} value={requestForm.type_conge} onChange={(event) => { setRequestForm((value) => ({ ...value, type_conge: event.target.value })); setRequestErrors((value) => ({ ...value, type_conge: '' })); }} required><option value="">Choisir un type</option>{types.filter((type) => type.actif).map((type) => <option key={type.id} value={type.id}>{type.libelle}</option>)}</select>{requestErrors.type_conge && <small className="field-error" id="type_conge-error">{requestErrors.type_conge}</small>}{types.length === 0 && <small>Les types de congé ne sont pas accessibles à ce compte.</small>}</label>
                <label className="form-field">Date de début<input id="date_debut" type="date" aria-invalid={Boolean(requestErrors.date_debut)} aria-describedby={requestErrors.date_debut ? 'date_debut-error' : undefined} value={requestForm.date_debut} onChange={(event) => { setRequestForm((value) => ({ ...value, date_debut: event.target.value })); setRequestErrors((value) => ({ ...value, date_debut: '' })); }} required />{requestErrors.date_debut && <small className="field-error" id="date_debut-error">{requestErrors.date_debut}</small>}</label>
                <label className="form-field">Date de fin<input id="date_fin" type="date" min={requestForm.date_debut || undefined} aria-invalid={Boolean(requestErrors.date_fin)} aria-describedby={requestErrors.date_fin ? 'date_fin-error' : undefined} value={requestForm.date_fin} onChange={(event) => { setRequestForm((value) => ({ ...value, date_fin: event.target.value })); setRequestErrors((value) => ({ ...value, date_fin: '' })); }} required />{requestErrors.date_fin && <small className="field-error" id="date_fin-error">{requestErrors.date_fin}</small>}</label>
                <label className="form-field leave-wide">Motif<textarea id="motif" rows="3" aria-invalid={Boolean(requestErrors.motif)} aria-describedby={requestErrors.motif ? 'motif-error' : undefined} value={requestForm.motif} onChange={(event) => { setRequestForm((value) => ({ ...value, motif: event.target.value })); setRequestErrors((value) => ({ ...value, motif: '' })); }} required />{requestErrors.motif && <small className="field-error" id="motif-error">{requestErrors.motif}</small>}</label>
              </fieldset>
              <div className="form-footer"><button type="button" className="outline-button" disabled={saving} onClick={() => setFormOpen(false)}>Annuler</button><button type="submit" className="primary-button" disabled={saving || types.filter((type) => type.actif).length === 0} aria-busy={saving}>{saving ? 'Envoi…' : 'Envoyer la demande'}</button></div>
            </form>
          </section>
        )}

        {activeTab === 'requests' && canReadRequests && (
          <section className="content-card">
            <div className="card-heading">
              <div>
                <h2>{canViewAll ? 'Demandes reçues' : 'Mes demandes'}</h2>
                <p>{loading ? 'Chargement…' : `${requests.length} demande${requests.length === 1 ? '' : 's'}`}</p>
              </div>
              <button type="button" className="outline-button" onClick={loadData} disabled={loading}>Actualiser</button>
            </div>
            {loading ? (
              <p className="leave-state" role="status">Chargement des demandes…</p>
            ) : sortedRequests.length === 0 ? (
              <div className="directory-empty">
                <strong>Aucune demande à afficher</strong>
                <p>Les demandes de congé apparaîtront ici.</p>
              </div>
            ) : (
              <div className="leave-request-list">
                {sortedRequests.map((request) => (
                  <article className="leave-request-card" key={request.id}>
                    <div className="leave-request-main">
                      <span className={`leave-status status-${request.statut.toLowerCase()}`}>{request.statut.replace('_', ' ')}</span>
                      <h3>{request.type_conge_libelle || `Type #${request.type_conge}`}</h3>
                      <p>{humanDate(request.date_debut)} – {humanDate(request.date_fin)}</p>
                      <p><strong>{employeeLabel(request)}</strong></p>
                      <p className="leave-request-meta">{request.motif}</p>
                      <button type="button" className="outline-button small-button" onClick={() => setDetailRequestId(request.id)}>
                        Voir le détail
                      </button>
                    </div>
                    {request.statut === 'EN_ATTENTE' && (
                      <div className="leave-request-actions">
                        {canDecide && <>
                          <button type="button" className="primary-button small-button" disabled={actionBusy} onClick={() => setPendingAction({ request, action: 'valider' })}>Valider</button>
                          <button type="button" className="outline-button small-button" disabled={actionBusy} onClick={() => setPendingAction({ request, action: 'refuser' })}>Refuser</button>
                        </>}
                        {(canDecide || String(request.employe) === String(user.id)) && (
                          <button type="button" className="outline-button small-button" disabled={actionBusy} onClick={() => setPendingAction({ request, action: 'supprimer' })}>Supprimer</button>
                        )}
                      </div>
                    )}
                  </article>
                ))}
              </div>
            )}
          </section>
        )}

        {activeTab === 'planning' && canReadRequests && (
          <LeavePlanning
            canViewAll={canViewAll}
            month={month}
            setMonth={setMonth}
            events={events}
            loading={planningLoading}
            error={planningError}
            onRetry={loadData}
          />
        )}

        {activeTab === 'balances' && canReadBalances && (
          <LeaveBalanceManager balances={balances} year={currentYear} loading={loading}
            onYearChange={(year) => setMonth((value) => new Date(year, value.getMonth(), 1))} />
        )}

        {activeTab === 'types' && canReadTypes && (
          <LeaveTypeManager types={types} loading={loading} onChanged={loadData} />
        )}

    </>
  );
}
