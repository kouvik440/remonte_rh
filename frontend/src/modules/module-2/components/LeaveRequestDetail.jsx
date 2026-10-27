import React, { useEffect, useId, useRef, useState } from 'react';
import { apiRequest, formatApiError } from '../../../shared/lib/api.js';

function useRequestDetail(requestId) {
  const [state, setState] = useState({ loading: true, detail: null, error: '' });
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    setState({ loading: true, detail: null, error: '' });
    apiRequest(`/api/demandes-absence/${requestId}/`).then(
      (detail) => { if (active) setState({ loading: false, detail, error: '' }); },
      (error) => {
        if (active) setState({ loading: false, detail: null, error: formatApiError(error.details || error.message) });
      },
    );
    return () => { active = false; };
  }, [requestId, attempt]);
  return { ...state, retry: () => setAttempt((value) => value + 1) };
}

const formatDate = (value, withTime = false) => value
  ? new Intl.DateTimeFormat('fr-FR', {
    dateStyle: 'long', ...(withTime ? { timeStyle: 'short' } : {}),
  }).format(new Date(withTime ? value : `${value}T12:00:00`))
  : 'Non renseignée';

/** @param {{ requestId: number | string, onClose: Function }} props */
export default function LeaveRequestDetail({ requestId, onClose }) {
  const { loading, detail, error, retry } = useRequestDetail(requestId);
  const dialogRef = useRef(null);
  const titleId = useId();
  useEffect(() => {
    const dialog = dialogRef.current;
    dialog.showModal();
    return () => dialog.close();
  }, []);
  return (
    <dialog ref={dialogRef} className="leave-detail-dialog" aria-labelledby={titleId}
      onCancel={(event) => { event.preventDefault(); onClose(); }}>
      <h2 id={titleId}>Détail de la demande #{requestId}</h2>
      {loading && <p role="status">Chargement du détail…</p>}
      {error && <div role="alert"><p>{error}</p><button type="button" className="outline-button" onClick={retry}>Réessayer</button></div>}
      {detail && <RequestInformation detail={detail} />}
      <div className="form-footer">
        <button type="button" className="outline-button" onClick={onClose} autoFocus>Fermer</button>
      </div>
    </dialog>
  );
}

/** @param {{ detail: Object }} props */
function RequestInformation({ detail }) {
  const employeeName = [detail.employe_prenom, detail.employe_nom].filter(Boolean).join(' ');
  const reviewerName = [detail.valideur_prenom, detail.valideur_nom].filter(Boolean).join(' ');
  const fields = [
    ['Employé', employeeName || `Employé #${detail.employe}`],
    ['Matricule', detail.employe_matricule || 'Non renseigné'],
    ['Département', detail.departement_nom || 'Non renseigné'],
    ['Type de congé', detail.type_conge_libelle || 'Congé'],
    ['Date de début', formatDate(detail.date_debut)],
    ['Date de fin', formatDate(detail.date_fin)],
    ['Motif', detail.motif],
    ['Statut', detail.statut?.replaceAll('_', ' ')],
    ['Date de demande', formatDate(detail.date_demande, true)],
    ['Décision prise par', reviewerName || (detail.valideur ? `Employé #${detail.valideur}` : 'Aucun valideur renseigné')],
    ['Date de décision', formatDate(detail.date_validation, true)],
  ];
  return <dl className="leave-detail-fields">{fields.map(([label, value]) => (
    <div key={label}><dt>{label}</dt><dd>{value}</dd></div>
  ))}</dl>;
}
