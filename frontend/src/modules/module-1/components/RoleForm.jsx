import React from 'react';

export default function RoleForm({
  form,
  setForm,
  permissions,
  canReadPermissions,
  saving,
  mode,
  onSubmit,
  onCancel,
  fieldErrors = {},
}) {
  const isEditing = mode === 'edit';

  const togglePermission = (permissionId) => {
    setForm((current) => ({
      ...current,
      permissions: current.permissions.includes(permissionId)
        ? current.permissions.filter((id) => id !== permissionId)
        : [...current.permissions, permissionId],
    }));
  };

  return (
    <section className="content-card employee-editor" aria-labelledby="roleFormTitle">
      <div className="card-heading editor-heading">
        <div>
          <span className="editor-kicker">CONFIGURATION DES ACCÈS</span>
          <h2 id="roleFormTitle">{isEditing ? 'Modifier le rôle' : 'Nouveau rôle'}</h2>
          <p>Choisissez un nom et les permissions nécessaires à ce rôle.</p>
        </div>
        <button type="button" className="icon-button close-editor" onClick={onCancel} disabled={saving} aria-label="Fermer">×</button>
      </div>

      <form className="employee-form" onSubmit={onSubmit} aria-busy={saving}>
        <fieldset className="role-form-fields" disabled={saving}>
          <div className="form-grid">
            <div className="form-field">
              <label htmlFor="roleName">Nom du rôle <i>*</i></label>
              <input
                id="roleName"
                maxLength="100"
                value={form.nom}
                onChange={(event) => setForm((current) => ({ ...current, nom: event.target.value }))}
                aria-invalid={Boolean(fieldErrors.nom)}
                aria-describedby={fieldErrors.nom ? 'roleNameError' : undefined}
                placeholder="Ex. GESTIONNAIRE_PAIE"
                required
              />
              {fieldErrors.nom && <small className="field-error" id="roleNameError">{fieldErrors.nom}</small>}
            </div>
            <div className="form-field">
              <label htmlFor="roleDescription">Description</label>
              <input
                id="roleDescription"
                maxLength="255"
                value={form.description}
                onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
                aria-invalid={Boolean(fieldErrors.description)}
                aria-describedby={fieldErrors.description ? 'roleDescriptionError' : undefined}
                placeholder="Responsabilités de ce rôle"
              />
              {fieldErrors.description && <small className="field-error" id="roleDescriptionError">{fieldErrors.description}</small>}
            </div>
          </div>
        </fieldset>

        <fieldset className="permission-fieldset role-permission-fieldset" disabled={saving || !canReadPermissions}>
          <legend>Permissions disponibles</legend>
          <p className="field-hint">Les autorisations sont appliquées par l’API selon le rôle de chaque utilisateur.</p>
          {!canReadPermissions ? (
            <p className="subtext">Votre compte ne peut pas consulter les permissions ; les permissions actuelles seront conservées.</p>
          ) : permissions.length === 0 ? (
            <p className="subtext">Aucune permission n’est disponible.</p>
          ) : (
            <div className="permission-grid">
              {permissions.map((permission) => {
                const id = Number(permission.id);
                return (
                  <label className="permission-option" key={permission.id}>
                    <input type="checkbox" checked={form.permissions.includes(id)} onChange={() => togglePermission(id)} />
                    <span><strong>{permission.nom}</strong><code>{permission.code}</code></span>
                  </label>
                );
              })}
            </div>
          )}
          {fieldErrors.permissions && <small className="field-error">{fieldErrors.permissions}</small>}
        </fieldset>

        <div className="form-footer">
          <button type="button" className="outline-button" onClick={onCancel} disabled={saving}>Annuler</button>
          <button type="submit" className="primary-button" disabled={saving || (!isEditing && (!canReadPermissions || permissions.length === 0))}>
            {saving ? 'Enregistrement…' : isEditing ? 'Enregistrer les modifications' : 'Créer le rôle'}
          </button>
        </div>
      </form>
    </section>
  );
}
