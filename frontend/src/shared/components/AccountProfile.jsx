import React, { useEffect, useRef, useState } from 'react';
import { navigate } from '../lib/navigation.js';
import { apiRequest, clearSession, formatApiError } from '../lib/api.js';
import ModalDialog from './ModalDialog.jsx';
import FormField from './FormField.jsx';

export default function AccountProfile({ onClose, onSaved }) {
  const [profile, setProfile] = useState(null);
  const [password, setPassword] = useState({ ancien_mot_de_passe: '', nouveau_mot_de_passe: '', confirmation: '' });
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [errors, setErrors] = useState({});
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const lock = useRef(false);
  function failure(cause) {
    if (cause.status === 401) {
      clearSession(); navigate('/connexion?session=expired', { replace: true });
    } else {
      setErrors(cause.details || {});
      setError(formatApiError(cause.details || cause.message));
    }
  }
  useEffect(() => {
    let current = true;
    apiRequest('/api/auth/me/').then((user) => { if (current) setProfile(user); })
      .catch((cause) => { if (current) failure(cause); })
      .finally(() => { if (current) setLoading(false); });
    return () => { current = false; };
  }, []);
  async function save(event, changingPassword) {
    event.preventDefault();
    if (lock.current) return;
    lock.current = true; setBusy(true); setErrors({}); setError(''); setNotice('');
    try {
      const result = await apiRequest(changingPassword ? '/api/auth/password/' : '/api/auth/me/', {
        method: changingPassword ? 'POST' : 'PATCH', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(changingPassword ? password : { nom: profile.nom, prenom: profile.prenom }),
      });
      if (changingPassword) {
        clearSession(); navigate('/connexion?password=changed', { replace: true });
      } else {
        localStorage.setItem('user', JSON.stringify(result));
        setProfile(result); onSaved(result); setNotice('Vos informations ont été enregistrées.');
      }
    } catch (cause) { failure(cause); }
    finally { lock.current = false; setBusy(false); }
  }
  return <ModalDialog title="Mon profil" busy={busy} onClose={onClose}>
    {loading && <p role="status">Chargement de votre profil…</p>}
    {error && <p className="message-box error" role="alert">{error}</p>}
    {notice && <p className="message-box success" role="status">{notice}</p>}
    {profile && <>
      <p>Compte : {profile.email}</p>
      <form onSubmit={(event) => save(event, false)} aria-busy={busy}>
        <fieldset className="leave-form-grid" disabled={busy}>
          <legend>Mes informations</legend>
          <FormField label="Nom" error={errors.nom}>{(props) => <input {...props} aria-label="Nom" value={profile.nom} required maxLength={100} autoComplete="family-name" onChange={(event) => setProfile({ ...profile, nom: event.target.value })} />}</FormField>
          <FormField label="Prénom" error={errors.prenom}>{(props) => <input {...props} aria-label="Prénom" value={profile.prenom} required maxLength={100} autoComplete="given-name" onChange={(event) => setProfile({ ...profile, prenom: event.target.value })} />}</FormField>
        </fieldset>
        <div className="form-footer"><button className="primary-button" type="submit" disabled={busy}>Enregistrer mes informations</button></div>
      </form>
      <form onSubmit={(event) => save(event, true)} aria-busy={busy}>
        <p>Après votre première connexion, choisissez un mot de passe personnel. Vous devrez vous reconnecter après sa modification.</p>
        <fieldset className="leave-form-grid" disabled={busy}>
          <legend>Changer mon mot de passe</legend>
          {[
            ['ancien_mot_de_passe', 'Mot de passe actuel', 'current-password'],
            ['nouveau_mot_de_passe', 'Nouveau mot de passe', 'new-password'],
            ['confirmation', 'Confirmer le nouveau mot de passe', 'new-password'],
          ].map(([name, label, autocomplete]) => <FormField key={name} label={label} error={errors[name]}>{(props) => <input {...props} aria-label={label} type="password" required autoComplete={autocomplete} value={password[name]} onChange={(event) => setPassword({ ...password, [name]: event.target.value })} />}</FormField>)}
        </fieldset>
        <div className="form-footer"><button className="primary-button" type="submit" disabled={busy}>Modifier mon mot de passe</button></div>
      </form>
    </>}
    <div className="form-footer"><button className="outline-button" type="button" disabled={busy} onClick={onClose}>Fermer</button></div>
  </ModalDialog>;
}
