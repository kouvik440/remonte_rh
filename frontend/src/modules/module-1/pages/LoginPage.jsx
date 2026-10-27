import React, { useState } from 'react';
import { navigate } from '../../../shared/lib/navigation.js';
import { homePath } from '../../../shared/lib/homePath.js';
import { login } from '../../../shared/lib/api.js';
import ThemeToggle from '../../../shared/components/ThemeToggle.jsx';
import AppLink from '../../../shared/components/AppLink.jsx';

export default function LoginPage() {
  const sessionReason = new URLSearchParams(window.location.search).get('session');
  const passwordChanged = new URLSearchParams(window.location.search).get('password') === 'changed';
  const initialMessage = sessionReason === 'expired'
    ? 'Votre session a expiré. Reconnectez-vous pour continuer.'
    : sessionReason === 'permissions'
      ? 'Reconnectez-vous pour charger vos autorisations actualisées.'
      : passwordChanged ? 'Votre mot de passe a été modifié. Connectez-vous avec votre nouveau mot de passe.' : '';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [message, setMessage] = useState(initialMessage);
  const [busy, setBusy] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setMessage('');
    setBusy(true);

    try {
      const user = await login(email.trim(), password, rememberMe);
      navigate(homePath(user), { replace: true });
    } catch (error) {
      setMessage(
        error instanceof TypeError
          ? 'Impossible de joindre le serveur. Vérifiez que Django est démarré, puis réessayez.'
          : error.message || 'Une erreur est survenue lors de la connexion.'
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="login-page">
      <div className="login-layout">
        
        {/* Section de présentation (Gauche) */}
        <section className="login-intro" aria-label="Présentation de Remonte RH">
          <AppLink className="login-brand" href="/connexion" aria-label="Remonte RH, accueil">
            <span className="login-brand-mark">RH</span>
            <span><strong>remonte</strong><small>GESTION RH</small></span>
          </AppLink>
          <div className="login-intro-copy">
            <span className="login-kicker">VOTRE ESPACE DE TRAVAIL</span>
            <h1>La gestion RH,<br />plus claire au quotidien.</h1>
            <p>Retrouvez les informations et les outils de gestion de votre équipe dans un espace sécurisé.</p>
          </div>
          <div className="login-intro-footer">
            <span className="login-status-dot" /> Espace de gestion des ressources humaines
          </div>
        </section>

        {/* Section du formulaire de connexion (Droite) */}
        <section className="login-content" aria-labelledby="loginTitle">
          <div className="login-theme-control"><ThemeToggle /></div>
          <div className="login-card">
            <div className="login-heading">
              <span className="login-mobile-mark">RH</span>
              <p className="login-eyebrow">ESPACE PERSONNEL</p>
              <h2 id="loginTitle">Connexion</h2>
              <p>Entrez vos identifiants pour accéder à votre espace Remonte RH.</p>
            </div>

            <form className="login-form" onSubmit={submit}>
              <div className="login-field">
                <label htmlFor="email">Adresse email</label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="username"
                  placeholder="nom@entreprise.com"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                />
              </div>

              <div className="login-field">
                <div className="login-label-row">
                  <label htmlFor="password">Mot de passe</label>
                </div>
                <div className="password-input-wrap">
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="current-password"
                    placeholder="Saisissez votre mot de passe"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    required
                  />
                  <button
                    className="password-toggle"
                    type="button"
                    aria-label={showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
                    aria-pressed={showPassword}
                    onClick={() => setShowPassword((shown) => !shown)}
                  >
                    {showPassword ? 'Masquer' : 'Afficher'}
                  </button>
                </div>
              </div>

              {/* Optionnel : Option Se souvenir de moi */}
              <div className="login-field-checkbox">
                <input
                  id="remember"
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                />
                <label htmlFor="remember">Se souvenir de moi</label>
              </div>

              <button className="login-submit" type="submit" disabled={busy} aria-busy={busy}>
                <span>{busy ? 'Connexion en cours…' : 'Se connecter'}</span>
                <span aria-hidden="true">→</span>
              </button>
            </form>

            {message && (
              <div className="message-box error login-message" role="alert" aria-live="polite">
                {message}
              </div>
            )}

            <p className="login-security">
              <span aria-hidden="true">✓</span>
              <span>Connexion sécurisée à votre espace RH</span>
            </p>
          </div>

          <footer className="login-footer">
            Remonte RH <span>·</span> Gestion des ressources humaines
          </footer>
        </section>

      </div>
    </main>
  );
}
