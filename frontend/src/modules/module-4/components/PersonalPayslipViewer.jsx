import React, { useEffect, useState } from 'react';
import { navigate } from '../../../shared/lib/navigation.js';
import ModalDialog from '../../../shared/components/ModalDialog.jsx';
import { apiRequest, clearSession, formatApiError } from '../../../shared/lib/api.js';

export default function PersonalPayslipViewer({ payroll, onClose }) {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');
  useEffect(() => {
    let current = true;
    let objectUrl;
    apiRequest(`/api/paiements/${payroll.id}/bulletin/`, { responseType: 'blob', headers: { Accept: '*/*' } }).then((blob) => {
      if (!current) return;
      if (blob.type.split(';')[0] !== 'application/pdf') throw new Error('Le fichier reçu n’est pas un bulletin PDF.');
      objectUrl = URL.createObjectURL(blob);
      setUrl(objectUrl);
    }).catch((failure) => {
      if (!current) return;
      if (failure.status === 401) { clearSession(); navigate('/connexion?session=expired', { replace: true }); }
      else setError(formatApiError(failure.details || failure.message));
    });
    return () => { current = false; if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [payroll.id]);
  return <ModalDialog title={`Mon bulletin de paie — ${payroll.periode}`} onClose={onClose}>
    {!url && !error && <p role="status">Chargement de votre bulletin…</p>}
    {error && <p className="message-box error" role="alert">{error}</p>}
    {url && <>
      <p>Vous pouvez consulter le PDF ci-dessous, l’ouvrir dans un onglet ou le télécharger.</p>
      <iframe className="personal-payslip-preview" src={url} title={`Fiche de paie de ${payroll.periode}`} />
    </>}
    <div className="form-footer personal-payslip-actions">
      {url && <>
        <a className="outline-button" href={url} target="_blank" rel="noopener noreferrer">Ouvrir le PDF dans un onglet</a>
        <a className="primary-button" href={url} download={`bulletin-paie-${payroll.periode}.pdf`}>Télécharger le PDF</a>
      </>}
      <button className="outline-button" type="button" onClick={onClose}>Fermer</button>
    </div>
  </ModalDialog>;
}
