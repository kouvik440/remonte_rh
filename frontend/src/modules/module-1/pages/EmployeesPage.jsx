import React, { useEffect, useMemo, useRef, useState, useCallback } from 'react';
import { navigate } from '../../../shared/lib/navigation.js';
import { Check, Pencil, Trash2 } from 'lucide-react';
import DeleteConfirmation from '../../../shared/components/DeleteConfirmation.jsx';
import EmployeeContracts from '../components/EmployeeContracts.jsx';
import ContractTypeManager from '../components/ContractTypeManager.jsx';
import EmployeeHistory from '../components/EmployeeHistory.jsx';
import PositionManager from '../components/PositionManager.jsx';
import { apiRequest, clearSession, formatApiError, getUser, hasPermission } from '../../../shared/lib/api.js';

const blankEmployee = () => ({
  matricule: '', nom: '', prenom: '', email: '', date_naissance: '',
  adresse: '', telephone: '', num_secu_sociale: '', date_entree: '',
  date_sortie: '', statut: 'ACTIF', department: '', responsable: '', password: '', roles: []
});

const statusLabel = (status) => ({
  ACTIF: 'Actif',
  INACTIF: 'Inactif',
  SUSPENDU: 'Suspendu'
}[status] || status || 'Non renseigné');

export default function EmployeesPage() {
  const user = useMemo(() => getUser(), []);
  const [employees, setEmployees] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [roles, setRoles] = useState([]);
  const [query, setQuery] = useState('');
  const [departmentFilter, setDepartmentFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [positionFilter, setPositionFilter] = useState('');
  const [contractFilter, setContractFilter] = useState('');
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [historyEmployee, setHistoryEmployee] = useState(null);
  const [positionsOpen, setPositionsOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(blankEmployee);
  const [editorOpen, setEditorOpen] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState(false);
  const [employeeToDelete, setEmployeeToDelete] = useState(null);
  const [contractsEmployee, setContractsEmployee] = useState(null);
  const [contractTypesOpen, setContractTypesOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deletingEmployeeId, setDeletingEmployeeId] = useState(null);
  const [fieldErrors, setFieldErrors] = useState({});
  const editorRef = useRef(null);
  const notificationTimer = useRef(null);

  const canRead = hasPermission('employe.read');
  const canCreate = hasPermission('employe.create');
  const canUpdate = hasPermission('employe.update');
  const canDelete = hasPermission('employe.delete');
  const canAssignRoles = hasPermission('employe.assign_roles') && hasPermission('role.read');

  const notify = useCallback((text, isError = false) => {
    window.clearTimeout(notificationTimer.current);
    setMessage(text);
    setError(isError);
    notificationTimer.current = window.setTimeout(() => {
      setMessage('');
      notificationTimer.current = null;
    }, 5000);
  }, []);

  useEffect(() => () => window.clearTimeout(notificationTimer.current), []);
  useEffect(() => {
    if (positionFilter && positionFilter !== '__none__' && !employees.some((item) => item.postes_actuels?.some((position) => position.nom === positionFilter))) setPositionFilter('');
    if (contractFilter && contractFilter !== '__none__' && !employees.some((item) => item.types_contrat_actuels?.some((type) => String(type.id) === contractFilter))) setContractFilter('');
  }, [employees, positionFilter, contractFilter]);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const tasks = [];
      if (canRead) tasks.push(apiRequest('/api/employes/').then((data) => setEmployees(Array.isArray(data) ? data : [])));
      if (hasPermission('departement.read')) tasks.push(apiRequest('/api/departements/').then((data) => setDepartments(Array.isArray(data) ? data : [])).catch((e) => { if (e.status !== 403) throw e; }));
      if (canAssignRoles) tasks.push(apiRequest('/api/roles/').then((data) => setRoles(Array.isArray(data) ? data : [])).catch((e) => { if (e.status !== 403) throw e; }));
      await Promise.all(tasks);
    } catch (e) {
      if (e.status === 401) {
        clearSession();
        navigate('/connexion?session=expired', { replace: true });
      } else {
        notify(`Impossible de charger les données : ${e.message}`, true);
      }
    } finally {
      setLoading(false);
    }
  }, [canRead, canAssignRoles, notify]);

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

  useEffect(() => {
    if (!editorOpen) return undefined;
    const frame = window.requestAnimationFrame(() => {
      editorRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      editorRef.current?.querySelector('input:not([type="hidden"]), select, textarea')?.focus({ preventScroll: true });
    });
    return () => window.cancelAnimationFrame(frame);
  }, [editorOpen]);

  const visibleEmployees = useMemo(() => employees.filter((employee) => {
    const normalizedQuery = query.trim().toLocaleLowerCase('fr');
    const haystack = [employee.nom, employee.prenom, employee.email, employee.matricule].join(' ').toLocaleLowerCase('fr');
    return (!normalizedQuery || haystack.includes(normalizedQuery))
      && (!departmentFilter || String(employee.department ?? '') === departmentFilter)
      && (!positionFilter || (positionFilter === '__none__' ? !employee.postes_actuels?.length : employee.postes_actuels?.some((position) => position.nom === positionFilter)))
      && (!contractFilter || (contractFilter === '__none__' ? !employee.types_contrat_actuels?.length : employee.types_contrat_actuels?.some((item) => String(item.id) === contractFilter)))
      && (!statusFilter || employee.statut === statusFilter);
  }), [employees, query, departmentFilter, statusFilter, positionFilter, contractFilter]);
  const positions = [...new Set(employees.flatMap((item) => (item.postes_actuels || []).map((position) => position.nom)))].sort((a, b) => a.localeCompare(b, 'fr'));
  const currentContractTypes = [...new Map(employees.flatMap((item) => item.types_contrat_actuels || []).map((item) => [item.id, item])).values()].sort((a, b) => a.libelle.localeCompare(b.libelle, 'fr'));

  const activeCount = useMemo(
    () => employees.filter((employee) => employee.statut === 'ACTIF' && employee.is_active !== false).length,
    [employees]
  );

  const openCreate = () => { setEditingId(null); setForm(blankEmployee()); setEditorOpen(true); };
  
  const openEdit = (employee) => {
    setEditingId(employee.id);
    setForm({
      ...blankEmployee(),
      ...employee,
      department: employee.department ? String(employee.department) : '',
      responsable: employee.responsable ? String(employee.responsable) : '',
      password: '',
      roles: (employee.roles || []).map(Number)
    });
    setEditorOpen(true);
  };

  const updateField = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
    setFieldErrors((current) => ({ ...current, [name]: undefined }));
  };

  const saveEmployee = async (event) => {
    event.preventDefault();
    if (saving) return;
    const action = editingId ? 'update' : 'create';
    if (!hasPermission(`employe.${action}`)) {
      return notify(`Votre compte ne possède pas la permission employe.${action}.`, true);
    }

    const payload = {
      matricule: form.matricule.trim(),
      nom: form.nom.trim(),
      prenom: form.prenom.trim(),
      email: form.email.trim(),
      date_naissance: form.date_naissance,
      adresse: form.adresse.trim(),
      telephone: form.telephone.trim(),
      num_secu_sociale: form.num_secu_sociale.trim(),
      date_entree: form.date_entree,
      date_sortie: form.date_sortie || null,
      statut: form.statut,
      is_active: form.statut === 'ACTIF',
      department: form.department ? Number(form.department) : null,
      responsable: form.responsable ? Number(form.responsable) : null,
    };
    if (canAssignRoles) payload.roles = form.roles.map(Number);
    if (form.password) payload.password = form.password;

    setSaving(true);
    setFieldErrors({});
    try {
      const result = await apiRequest(editingId ? `/api/employes/${editingId}/` : '/api/employes/', {
        method: editingId ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      notify(editingId ? 'Le dossier employé a été mis à jour.' : `Le compte de ${result.prenom} ${result.nom} a été créé.`);
      setEditorOpen(false);
      await loadData();
    } catch (e) {
      if (e.details && typeof e.details === 'object') setFieldErrors(e.details);
      notify(`Enregistrement impossible : ${formatApiError(e.details || e.message)}`, true);
    } finally {
      setSaving(false);
    }
  };

  const deleteEmployee = async (employee) => {
    if (!canDelete || deletingEmployeeId !== null) return;


    setDeletingEmployeeId(employee.id);
    try {
      await apiRequest(`/api/employes/${employee.id}/`, { method: 'DELETE' });
      notify(`Le dossier de ${employee.prenom} ${employee.nom} a été supprimé.`);
      setEmployeeToDelete(null);
      await loadData();
    } catch (e) {
      setEmployeeToDelete(null);
      notify(`Suppression impossible : ${formatApiError(e.details || e.message)}`, true);
    } finally {
      setDeletingEmployeeId(null);
    }
  };

  if (!localStorage.getItem('access_token')) return null;

  return (
    <>
      <>
        {contractsEmployee && <EmployeeContracts employee={contractsEmployee} onClose={() => { setContractsEmployee(null); loadData(); }} />}
        {historyEmployee && <EmployeeHistory employee={historyEmployee} onClose={() => setHistoryEmployee(null)} />}
        {positionsOpen && <PositionManager onClose={() => { setPositionsOpen(false); loadData(); }} />}
        {contractTypesOpen && <ContractTypeManager onClose={() => setContractTypesOpen(false)} />}
        {employeeToDelete && (
          <DeleteConfirmation
            description={`Supprimer ${employeeToDelete.prenom} ${employeeToDelete.nom} ? Les données RH rattachées à ce compte seront également supprimées. Cette action est irréversible.`}
            busy={deletingEmployeeId !== null}
            onCancel={() => setEmployeeToDelete(null)}
            onConfirm={() => deleteEmployee(employeeToDelete)}
          />
        )}
        <section className="page-heading">
          <div>
            <p className="eyebrow">Annuaire du personnel</p>
            <h1>Gestion des employés</h1>
          </div>
          <div className="leave-request-actions">
          {hasPermission('poste.read') && <button type="button" className="outline-button" onClick={() => setPositionsOpen(true)}>Postes</button>}
          {hasPermission('type_contrat.read') && <button type="button" className="outline-button" onClick={() => setContractTypesOpen(true)}>Types de contrat</button>}
          {canCreate && (
            <button type="button" className="primary-button" onClick={openCreate}>
              <span aria-hidden="true">＋</span><span className="employee-add-label">Ajouter un employé</span>
            </button>
          )}
          </div>
        </section>

        {!canRead && (
          <div className="message-box error">
            Votre compte ne possède pas la permission de consulter l’annuaire des employés.
          </div>
        )}
        {canRead && !canDelete && (
          <div className="message-box error" role="status">
            La suppression d’un employé nécessite la permission employe.delete. Si ce droit vient de vous être attribué, déconnectez-vous puis reconnectez-vous pour actualiser votre session.
          </div>
        )}

        {canRead && (
          <section className="employee-workspace">
            <div className="stats-grid" aria-label="Résumé de l’annuaire">
              <article className="stat-card">
                <div><span className="stat-label">Effectif total</span><strong>{employees.length}</strong><small>dans l’annuaire</small></div>
              </article>
              <article className="stat-card">
                <div><span className="stat-label">Employés actifs</span><strong>{activeCount}</strong><small>statut actif</small></div>
              </article>
              <article className="stat-card">
                <div><span className="stat-label">Autres statuts</span><strong>{employees.length - activeCount}</strong><small>inactifs ou suspendus</small></div>
              </article>
              <article className="stat-card">
                <div><span className="stat-label">Départements</span><strong>{hasPermission('departement.read') ? departments.length : '—'}</strong><small>référencés</small></div>
              </article>
            </div>

            <section className="content-card">
              <div className="card-heading">
                <div>
                  <h2>Annuaire des employés</h2>
                </div>
                <button type="button" className="outline-button" onClick={loadData}>
                  <span>↻</span> Actualiser
                </button>
              </div>

              <div className={`directory-toolbar${filtersOpen ? ' filters-expanded' : ''}`}>
                <label className="search-field">
                  <span aria-hidden="true">⌕</span>
                  <input type="search" placeholder="Rechercher un nom, matricule ou email…" aria-label="Rechercher un employé" value={query} onChange={(e) => setQuery(e.target.value)} />
                </label>
                <button type="button" className="outline-button directory-filter-toggle" aria-expanded={filtersOpen} aria-controls="employee-directory-filters" onClick={() => setFiltersOpen((value) => !value)}>Filtres{[positionFilter, contractFilter, departmentFilter, statusFilter].filter(Boolean).length ? ` (${[positionFilter, contractFilter, departmentFilter, statusFilter].filter(Boolean).length})` : ''}</button>
                <div id="employee-directory-filters" className="directory-filters">
                <label className="filter-field"><span>Poste</span><select aria-label="Filtrer par poste" value={positionFilter} onChange={(event) => setPositionFilter(event.target.value)}>
                  <option value="">Tous les postes</option><option value="__none__">Sans poste</option>
                  {positions.map((name) => <option key={name} value={name}>{name}</option>)}
                </select></label>
                <label className="filter-field"><span>Contrat en cours</span><select aria-label="Filtrer par type de contrat" value={contractFilter} onChange={(event) => setContractFilter(event.target.value)}>
                  <option value="">Tous les contrats</option><option value="__none__">Sans contrat en cours</option>
                  {currentContractTypes.map((item) => <option key={item.id} value={item.id}>{item.libelle}</option>)}
                </select></label>
                <label className="filter-field">
                  <span>Département</span>
                  <select value={departmentFilter} onChange={(e) => setDepartmentFilter(e.target.value)}>
                    <option value="">Tous les départements</option>
                    {departments.map((department) => (
                      <option key={department.id} value={department.id}>{department.nom}</option>
                    ))}
                  </select>
                </label>
                <label className="filter-field">
                  <span>Statut</span>
                  <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
                    <option value="">Tous les statuts</option>
                    <option value="ACTIF">Actif</option>
                    <option value="INACTIF">Inactif</option>
                    <option value="SUSPENDU">Suspendu</option>
                  </select>
                </label>
                </div>
              </div>

              <div className="directory-summary" aria-live="polite">
                {loading ? 'Chargement…' : `Affichage de ${visibleEmployees.length} sur ${employees.length} employé${employees.length === 1 ? '' : 's'}`}
              </div>

              <div className="table-wrapper employee-table-wrap">
                <table className="employee-table">
                  <thead>
                    <tr>
                      <th>Employé</th>
                      <th>Matricule</th>
                      <th>Département</th>
                      <th>Poste / responsable</th>
                      <th>Contrat en cours</th>
                      <th>Statut</th>
                      <th>Rôle(s)</th>
                      <th className="actions-heading">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {!loading && visibleEmployees.map((employee) => {
                      const department = departments.find((item) => Number(item.id) === Number(employee.department))?.nom || '—';
                      const roleNames = (employee.roles || []).map((id) => roles.find((role) => Number(role.id) === Number(id))?.nom || `Rôle ${id}`).join(', ') || '—';
                      const badge = employee.statut === 'ACTIF' ? 'status-active' : employee.statut === 'SUSPENDU' ? 'status-suspended' : 'status-inactive';
                      
                      return (
                        <tr key={employee.id}>
                          <td>
                            <div className="employee-person">
                              <span className="person-avatar">{`${employee.prenom?.[0] || ''}${employee.nom?.[0] || ''}`.toUpperCase()}</span>
                              <span className="person-detail"><strong>{employee.prenom} {employee.nom}</strong><small>{employee.email}</small></span>
                            </div>
                          </td>
                          <td><span className="employee-id">{employee.matricule || '—'}</span></td>
                          <td>{department}</td>
                          <td><div className="person-detail"><strong>{employee.poste_nom || 'Sans poste'}</strong><small>Responsable : {employee.responsable_nom || 'Non renseigné'}</small></div></td>
                          <td>{(employee.types_contrat_actuels || []).map((item) => item.libelle).join(', ') || '—'}</td>
                          <td><span className={`status-badge ${badge}`}><i />{statusLabel(employee.statut)}</span></td>
                          <td><span className="role-text">{roleNames}</span></td>
                          <td>
                            <div className="row-actions">
                              <button type="button" className="outline-button" onClick={() => setHistoryEmployee(employee)} aria-label={`Historique de ${employee.prenom} ${employee.nom}`}>Historique</button>
                              {hasPermission('contrat.read') && <button type="button" className="outline-button" onClick={() => setContractsEmployee(employee)} aria-label={`Contrats de ${employee.prenom} ${employee.nom}`}>Contrats</button>}
                              {canUpdate && <button type="button" className="row-icon-button" title="Modifier" aria-label={`Modifier ${employee.prenom} ${employee.nom}`} onClick={() => openEdit(employee)}><Pencil size={16} aria-hidden="true" /></button>}
                              {canDelete && <button type="button" className="row-icon-button delete-action" title="Supprimer" aria-label={`Supprimer ${employee.prenom} ${employee.nom}`} onClick={() => setEmployeeToDelete(employee)} disabled={deletingEmployeeId !== null} aria-busy={deletingEmployeeId === employee.id}>{deletingEmployeeId === employee.id ? '…' : <Trash2 size={16} aria-hidden="true" />}</button>}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {!loading && visibleEmployees.length === 0 && (
                <div className="directory-empty">
                  <span className="empty-icon">⌕</span>
                  <strong>Aucun employé trouvé</strong>
                  <p>Essayez d’ajuster votre recherche ou vos filtres.</p>
                </div>
              )}
            </section>
          </section>
        )}

        {editorOpen && (
          <section ref={editorRef} className="content-card employee-editor" aria-labelledby="employeeEditorTitle">
            <div className="card-heading editor-heading">
              <div>
                <span className="editor-kicker">DOSSIER EMPLOYÉ</span>
                <h2 id="employeeEditorTitle">{editingId ? 'Modifier un employé' : 'Nouvel employé'}</h2>
                <p>Les champs marqués d’un astérisque sont obligatoires.</p>
              </div>
              <button type="button" className="icon-button close-editor" onClick={() => setEditorOpen(false)} aria-label="Fermer le formulaire">×</button>
            </div>
            
            <form className="employee-form" onSubmit={saveEmployee}>
              <fieldset className="employee-form-fields" disabled={saving}>
                <div className="form-section-title"><span>01</span><div><strong>Informations personnelles</strong><small>Identité et coordonnées de l’employé</small></div></div>
                <div className="form-grid">
                  <Field label="Matricule" name="matricule" value={form.matricule} onChange={updateField} required placeholder="Ex. EMP-001" errors={fieldErrors} />
                  <Field label="Statut" name="statut" value={form.statut} onChange={updateField} type="select" options={ [['ACTIF','Actif'],['INACTIF','Inactif'],['SUSPENDU','Suspendu']] } />
                  <Field label="Nom" name="nom" value={form.nom} onChange={updateField} required errors={fieldErrors} />
                  <Field label="Prénom" name="prenom" value={form.prenom} onChange={updateField} required errors={fieldErrors} />
                  <Field label="Date de naissance" name="date_naissance" value={form.date_naissance || ''} onChange={updateField} type="date" required errors={fieldErrors} />
                  <Field label="Téléphone" name="telephone" value={form.telephone} onChange={updateField} required errors={fieldErrors} />
                  <Field label="N° de sécurité sociale" name="num_secu_sociale" value={form.num_secu_sociale} onChange={updateField} required errors={fieldErrors} />
                  <Field label="Adresse" name="adresse" value={form.adresse} onChange={updateField} type="textarea" wide errors={fieldErrors} />
                </div>

                <div className="form-section-title"><span>02</span><div><strong>Informations professionnelles</strong><small>Affectation et dates de présence</small></div></div>
                <div className="form-grid">
                  <Field label="Email professionnel" name="email" value={form.email} onChange={updateField} type="email" required errors={fieldErrors} />
                  <Field label="Département" name="department" value={form.department} onChange={updateField} type="select" options={ [['','Non renseigné'], ...departments.map((d) => [String(d.id), d.nom])] } errors={fieldErrors} />
                  <p className="field-hint">Le poste occupé est sélectionné dans le contrat de l’employé.</p>
                  <Field label="Responsable hiérarchique" name="responsable" value={form.responsable} onChange={updateField} type="select"
                    options={ [['', 'Aucun responsable'], ...employees.filter((item) => item.id !== editingId && (item.is_active || String(item.id) === form.responsable)).map((item) => [String(item.id), `${item.prenom} ${item.nom} · ${item.matricule}`])] } errors={fieldErrors} />
                  <Field label="Date d’entrée" name="date_entree" value={form.date_entree || ''} onChange={updateField} type="date" required errors={fieldErrors} />
                  <Field label="Date de sortie" name="date_sortie" value={form.date_sortie || ''} onChange={updateField} type="date" errors={fieldErrors} />
                  
                  {canAssignRoles && (
                    <div className="form-field form-field-wide role-assignment-field">
                      <div className="role-assignment-heading">
                        <label>Rôles attribués</label>
                        <span className="role-selection-count">{form.roles.length} sélectionné{form.roles.length === 1 ? '' : 's'}</span>
                      </div>
                      {roles.length ? (
                        <div className="role-checkbox-list">
                          {roles.map((role) => {
                            const selected = form.roles.some((id) => Number(id) === Number(role.id));
                            return (
                              <label className={`role-checkbox ${selected ? 'selected' : ''}`} key={role.id}>
                                <input
                                  type="checkbox"
                                  checked={selected}
                                  onChange={() => setForm((current) => ({
                                    ...current,
                                    roles: selected
                                      ? current.roles.filter((id) => Number(id) !== Number(role.id))
                                      : [...current.roles, Number(role.id)],
                                  }))}
                                />
                                <span className="role-checkbox-copy"><strong>{role.nom}</strong><small>{role.description || 'Aucune description'}</small></span>
                                <span className="role-checkbox-check" aria-hidden="true"><Check size={12} /></span>
                              </label>
                            );
                          })}
                        </div>
                      ) : (
                        <p className="field-hint">Aucun rôle disponible à attribuer.</p>
                      )}
                      <small className="field-hint">Tu peux attribuer plusieurs rôles au même employé.</small>
                    </div>
                  )}
                </div>

                <div className="form-section-title account-section"><span>03</span><div><strong>Accès au compte</strong><small>Identifiants de connexion</small></div></div>
                <div className="form-grid">
                  <Field label={editingId ? 'Nouveau mot de passe (facultatif)' : 'Mot de passe temporaire'} name="password" value={form.password} onChange={updateField} type="password" required={!editingId} wide errors={fieldErrors} />
                </div>
              </fieldset>

              <div className="form-footer">
                <button type="button" className="outline-button" onClick={() => setEditorOpen(false)} disabled={saving}>Annuler</button>
                <button type="submit" className="primary-button" disabled={saving}>
                  {saving ? 'Enregistrement…' : editingId ? 'Enregistrer les modifications' : 'Créer l’employé'} <span>→</span>
                </button>
              </div>
            </form>
          </section>
        )}

        {message && <div className={`message-box ${error ? 'error' : 'success'}`} role={error ? 'alert' : 'status'}>{message}</div>}
      </>
    </>
  );
}

function Field({ label, name, value, onChange, type = 'text', required = false, wide = false, placeholder = '', options = [], errors = {} }) {
  const fieldError = errors[name];
  const errorText = (Array.isArray(fieldError) ? fieldError : fieldError ? [fieldError] : []).join(' ');
  return (
    <div className={`form-field ${wide ? 'form-field-wide' : ''}`}>
      <label htmlFor={name}>{label}{required && <i> *</i>}</label>
      {type === 'select' ? (
        <select id={name} name={name} value={value} onChange={onChange} aria-invalid={Boolean(errorText)} aria-describedby={errorText ? `${name}-error` : undefined}>
          {options.map(([optionValue, optionLabel]) => <option key={optionValue} value={optionValue}>{optionLabel}</option>)}
        </select>
      ) : type === 'textarea' ? (
        <textarea id={name} name={name} value={value} onChange={onChange} required={required} rows="2" aria-invalid={Boolean(errorText)} aria-describedby={errorText ? `${name}-error` : undefined} />
      ) : (
        <input id={name} name={name} type={type} value={value ?? ''} onChange={onChange} required={required} placeholder={placeholder} autoComplete={name === 'password' ? 'new-password' : undefined} aria-invalid={Boolean(errorText)} aria-describedby={errorText ? `${name}-error` : undefined} />
      )}
      {errorText && <small className="field-error" id={`${name}-error`}>{errorText}</small>}
    </div>
  );
}
