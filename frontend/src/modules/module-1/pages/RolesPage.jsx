import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { navigate } from '../../../shared/lib/navigation.js';
import DeleteConfirmation from '../../../shared/components/DeleteConfirmation.jsx';
import { apiRequest, clearSession, formatApiError, getUser, hasPermission } from '../../../shared/lib/api.js';
import RoleForm from '../components/RoleForm.jsx';

const emptyForm = () => ({ nom: '', description: '', permissions: [] });
const initials = (name = '') => name.split(/[ _-]+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join('').toUpperCase() || 'RH';

const getFieldErrors = (details) => {
  if (!details || typeof details !== 'object' || Array.isArray(details)) return {};
  return Object.fromEntries(
    ['nom', 'description', 'permissions']
      .filter((field) => details[field])
      .map((field) => [field, (Array.isArray(details[field]) ? details[field] : [details[field]]).map(String).join(' ')])
  );
};

export default function RolesPage() {
  const user = useMemo(() => getUser(), []);
  const [roles, setRoles] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [editorMode, setEditorMode] = useState(null);
  const [editingRoleId, setEditingRoleId] = useState(null);
  const [fieldErrors, setFieldErrors] = useState({});
  const [roleToDelete, setRoleToDelete] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deletingRoleId, setDeletingRoleId] = useState(null);
  const [message, setMessage] = useState('');
  const [messageIsError, setMessageIsError] = useState(false);

  const canReadRoles = hasPermission('role.read');
  const canCreateRoles = hasPermission('role.create');
  const canUpdateRoles = hasPermission('role.update');
  const canDeleteRoles = hasPermission('role.delete');
  const canReadPermissions = hasPermission('permission.read');

  const notify = useCallback((text, isError = false) => {
    setMessage(text);
    setMessageIsError(isError);
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [roleData, permissionData] = await Promise.all([
        apiRequest('/api/roles/'),
        canReadPermissions ? apiRequest('/api/permissions/').catch((error) => {
          if (error.status !== 403) throw error;
          return [];
        }) : Promise.resolve([]),
      ]);
      setRoles(Array.isArray(roleData) ? roleData : []);
      setPermissions(Array.isArray(permissionData) ? permissionData : []);
    } catch (error) {
      if (error.status === 401) {
        clearSession();
        navigate('/connexion?session=expired', { replace: true });
      } else {
        notify(`Impossible de charger les rôles : ${formatApiError(error.details || error.message)}`, true);
      }
    } finally {
      setLoading(false);
    }
  }, [canReadPermissions, notify]);

  useEffect(() => {
    if (!localStorage.getItem('access_token')) {
      navigate('/connexion', { replace: true });
      return;
    }
    if (!Array.isArray(user.permissions)) {
      clearSession();
      navigate('/connexion?session=permissions', { replace: true });
      return;
    }
    if (canReadRoles) load();
    else setLoading(false);
  }, [canReadRoles, load, user]);

  const closeEditor = () => {
    if (saving) return;
    setEditorMode(null);
    setEditingRoleId(null);
    setFieldErrors({});
  };

  const openCreate = () => {
    setForm(emptyForm());
    setFieldErrors({});
    setEditingRoleId(null);
    setEditorMode('create');
  };

  const openEdit = (role) => {
    setForm({
      nom: role.nom || '',
      description: role.description || '',
      permissions: (role.permissions || []).map(Number),
    });
    setFieldErrors({});
    setEditingRoleId(role.id);
    setEditorMode('edit');
  };

  const saveRole = async (event) => {
    event.preventDefault();
    const isEditing = editorMode === 'edit';
    if (saving || (isEditing ? !canUpdateRoles : !canCreateRoles)) return;

    const payload = { nom: form.nom.trim(), description: form.description.trim() };
    if (canReadPermissions) payload.permissions = form.permissions;
    setSaving(true);
    setFieldErrors({});
    try {
      const savedRole = await apiRequest(
        isEditing ? `/api/roles/${editingRoleId}/` : '/api/roles/',
        {
          method: isEditing ? 'PUT' : 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        },
      );
      notify(isEditing ? `Le rôle « ${savedRole.nom} » a été modifié.` : `Le rôle « ${savedRole.nom} » a été créé.`);
      setEditorMode(null);
      setEditingRoleId(null);
      await load();
    } catch (error) {
      const nextFieldErrors = getFieldErrors(error.details);
      setFieldErrors(nextFieldErrors);
      notify(
        Object.keys(nextFieldErrors).length
          ? 'Le rôle n’a pas été enregistré. Corrigez les erreurs indiquées dans le formulaire.'
          : `Impossible d’enregistrer le rôle : ${formatApiError(error.details || error.message)}`,
        true,
      );
    } finally {
      setSaving(false);
    }
  };

  const deleteRole = async (role) => {
    if (!canDeleteRoles || deletingRoleId !== null) return;


    setDeletingRoleId(role.id);
    try {
      await apiRequest(`/api/roles/${role.id}/`, { method: 'DELETE' });
      notify(`Le rôle « ${role.nom} » a été supprimé.`);
      if (editingRoleId === role.id) closeEditor();
      setRoleToDelete(null);
      await load();
    } catch (error) {
      setRoleToDelete(null);
      notify(`Impossible de supprimer le rôle : ${formatApiError(error.details || error.message)}`, true);
    } finally {
      setDeletingRoleId(null);
    }
  };

  return (
    <>
      <>
        {roleToDelete && (
          <DeleteConfirmation
            description={`Supprimer le rôle « ${roleToDelete.nom} » ? Cette action retirera ce rôle des comptes auxquels il est attribué.`}
            busy={deletingRoleId !== null}
            onCancel={() => setRoleToDelete(null)}
            onConfirm={() => deleteRole(roleToDelete)}
          />
        )}
        <section className="page-heading">
          <div>
            <p className="eyebrow">SÉCURITÉ ET AUTORISATIONS</p>
            <h1>Rôles et accès</h1>
            <p className="page-description">Définissez les permissions associées à chaque rôle du personnel.</p>
          </div>
          {canCreateRoles && canReadPermissions && <button type="button" className="primary-button" onClick={openCreate}><span>＋</span> Créer un rôle</button>}
        </section>

        {message && <div className={`message-box ${messageIsError ? 'error' : 'success'}`} role={messageIsError ? 'alert' : 'status'}>{message}</div>}
        {!canReadRoles && <div className="message-box error" role="alert">Votre compte ne possède pas la permission role.read.</div>}
        {canReadRoles && (!canUpdateRoles || !canDeleteRoles) && <div className="message-box error" role="status">{!canUpdateRoles && 'Modifier un rôle nécessite role.update. '}{!canDeleteRoles && 'Supprimer un rôle nécessite role.delete. '}Si ce droit vient de vous être attribué, déconnectez-vous puis reconnectez-vous pour actualiser votre session.</div>}

        {editorMode && (
          <RoleForm
            form={form}
            setForm={setForm}
            permissions={permissions}
            canReadPermissions={canReadPermissions}
            saving={saving}
            mode={editorMode}
            onSubmit={saveRole}
            onCancel={closeEditor}
            fieldErrors={fieldErrors}
          />
        )}

        {canReadRoles && (
          <section className="content-card">
            <div className="card-heading">
              <div>
                <h2>Rôles existants</h2>
                <p>{loading ? 'Chargement des rôles…' : `${roles.length} rôle${roles.length === 1 ? '' : 's'} disponible${roles.length === 1 ? '' : 's'}`}</p>
              </div>
              <button type="button" className="outline-button" onClick={load} disabled={loading}><span>↻</span> Actualiser</button>
            </div>
            {loading ? <p className="leave-state" role="status">Chargement des rôles…</p> : roles.length > 0 ? (
              <div className="role-list">
                {roles.map((role) => {
                  const assigned = (role.permissions || [])
                    .map((id) => permissions.find((permission) => Number(permission.id) === Number(id)))
                    .filter(Boolean);
                  const isDeleting = deletingRoleId === role.id;
                  return (
                    <article className="role-card" key={role.id}>
                      <div className="role-card-top">
                        <span className="role-avatar">{initials(role.nom)}</span>
                        <div className="role-title"><h3>{role.nom}</h3><p>{role.description || 'Aucune description'}</p></div>
                        <span className="role-count">{role.permissions?.length || 0} permission{role.permissions?.length === 1 ? '' : 's'}</span>
                      </div>
                      <div className="role-permission-tags">
                        {assigned.length ? assigned.map((permission) => <span className="permission-tag" title={permission.code} key={permission.id}>{permission.nom}</span>) : <span className="role-no-permissions">{role.permissions?.length ? 'Permissions attribuées (détails non accessibles)' : 'Aucune permission attribuée'}</span>}
                      </div>
                      {(canUpdateRoles || canDeleteRoles) && (
                        <div className="role-actions">
                          {canUpdateRoles && <button type="button" className="outline-button small-button" onClick={() => openEdit(role)}>Modifier</button>}
                          {canDeleteRoles && <button type="button" className="danger-button small-button" onClick={() => setRoleToDelete(role)} disabled={deletingRoleId !== null} aria-busy={isDeleting}>{isDeleting ? 'Suppression…' : 'Supprimer'}</button>}
                        </div>
                      )}
                    </article>
                  );
                })}
              </div>
            ) : (
              <div className="directory-empty"><span className="empty-icon">♙</span><strong>Aucun rôle à afficher</strong><p>Les rôles accessibles apparaîtront ici.</p></div>
            )}
          </section>
        )}
      </>
    </>
  );
}
