import React, { useEffect, useState } from 'react';
import { navigate } from '../../../shared/lib/navigation.js';
import ModalDialog from '../../../shared/components/ModalDialog.jsx';
import useApiMutation from '../../../shared/hooks/useApiMutation.js';
import { clearSession, getUser, hasPermission } from '../../../shared/lib/api.js';
import DepartmentEditor from '../components/DepartmentEditor.jsx';
import DepartmentList from '../components/DepartmentList.jsx';
import useDepartments from '../hooks/useDepartments.js';

export default function DepartmentsPage() {
  const authenticated = Boolean(localStorage.getItem('access_token'));
  const validPermissions = Array.isArray(getUser().permissions);
  const canRead = hasPermission('departement.read');
  const data = useDepartments(authenticated && validPermissions && canRead);
  const mutation = useApiMutation(data.load);
  const [editor, setEditor] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const [notice, setNotice] = useState('');
  useEffect(() => {
    if (!authenticated) navigate('/connexion', { replace: true });
    else if (!validPermissions) {
      clearSession(); navigate('/connexion?session=permissions', { replace: true });
    }
  }, [authenticated, validPermissions]);
  const openEditor = (department) => {
    mutation.reset(); setNotice(''); setEditor({ department });
  };
  const remove = async () => {
    if (!hasPermission('departement.delete') || !deleting) return;
    if (await mutation.submit(`/api/departements/${deleting.id}/`, 'DELETE')) {
      setDeleting(null); setNotice('Département supprimé. Les employés sont conservés.');
    }
  };
  return <>
    <section className="page-heading">
      <div><p className="eyebrow">ORGANISATION DU PERSONNEL</p><h1>Départements</h1>
        <p className="page-description">Gérez les départements proposés dans les dossiers employés et les filtres.</p></div>
      {canRead && hasPermission('departement.create') && <button type="button" className="primary-button" disabled={mutation.saving} onClick={() => openEditor(null)}>Nouveau département</button>}
    </section>
    {notice && <p className="message-box success" role="status">{notice}</p>}
    {!canRead ? <p className="message-box error" role="alert">Vous n’avez pas accès à la consultation des départements.</p>
      : <section className="content-card" aria-busy={data.loading}>
        <div className="card-heading"><h2>Départements enregistrés</h2>
          <button type="button" className="outline-button" disabled={data.loading || mutation.saving} onClick={data.load}>Actualiser</button></div>
        {data.loading ? <p role="status">Chargement des départements…</p>
          : data.error ? <p className="message-box error" role="alert">{data.error}</p>
            : <DepartmentList departments={data.departments} busy={mutation.saving} onEdit={openEditor}
              onDelete={(department) => { mutation.reset(); setNotice(''); setDeleting(department); }} />}
      </section>}
    {canRead && editor && <DepartmentEditor department={editor.department} mutation={mutation} onClose={() => setEditor(null)}
      onSaved={() => { setEditor(null); setNotice('Département enregistré.'); }} />}
    {canRead && deleting && <ModalDialog title="Supprimer le département" busy={mutation.saving} onClose={() => setDeleting(null)}>
      <p>Supprimer « {deleting.nom} » ? Les employés seront conservés, mais leur affectation à ce département sera retirée. Les paies déjà calculées conservent leur département historique.</p>
      {mutation.message && <p className="message-box error" role="alert">{mutation.message}</p>}
      <div className="form-footer">
        <button type="button" className="outline-button" disabled={mutation.saving} onClick={() => setDeleting(null)}>Conserver</button>
        <button type="button" className="danger-button" disabled={mutation.saving} onClick={remove}>Confirmer la suppression</button>
      </div>
    </ModalDialog>}
  </>;
}
