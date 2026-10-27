import React, { useEffect, useRef, useState } from 'react';
import { navigate, pageRoutes } from '../lib/navigation.js';
import { Building2, CalendarDays, ChartNoAxesCombined, Clock3, FileText, Gauge, Landmark, LogOut, Menu, ShieldCheck, UsersRound, Wallet, X } from 'lucide-react';
import AccountProfile from './AccountProfile.jsx';
import ThemeToggle from './ThemeToggle.jsx';
import AppLink from './AppLink.jsx';
import { clearSession, getUser, hasPermission } from '../lib/api.js';
import { homePath } from '../lib/homePath.js';
import useBodyScrollLock from '../hooks/useBodyScrollLock.js';

const initials = (text = '') => text.split(/[\s_-]+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join('').toUpperCase() || 'RH';
const destinations = [
  { key: 'employees', label: 'Employés', icon: UsersRound, permissions: ['employe.read'] },
  { key: 'departments', label: 'Départements', icon: Building2, permissions: ['departement.read'] },
  { key: 'roles', label: 'Rôles et accès', icon: ShieldCheck, permissions: ['role.read'] },
  { key: 'leaves', label: 'Congés et absences', icon: CalendarDays, permissions: ['demande_absence.read', 'solde_conge.read', 'conge.read'] },
  { key: 'records', label: 'Coordonnées bancaires', icon: Landmark, permissions: ['coordonnees_bancaires.read'] },
  { key: 'payroll', label: 'Paie et virements', icon: Wallet, permissions: ['paie.read', 'ordre_virement.read'] },
  { key: 'payroll-mass', label: 'Masse salariale', icon: ChartNoAxesCombined, permissions: ['paie.read'] },
  { key: 'tgm', label: 'TGM et coûts projets', icon: Gauge, permissions: ['paie.read'] },
  { key: 'timesheets', label: 'Feuilles de temps', icon: Clock3, personal: true },
  { key: 'my-payslips', label: 'Mes bulletins de paie', icon: FileText, personal: true },
];

export default function AppLayout({ active, children, profileAvailable = true }) {
  const [user, setUser] = useState(getUser);
  const [profileOpen, setProfileOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [compact, setCompact] = useState(() => window.matchMedia('(max-width: 1100px)').matches);
  const menuButton = useRef(null);
  const sidebar = useRef(null);
  const displayName = `${user.prenom || ''} ${user.nom || ''}`.trim() || user.email || 'Espace RH';
  const badge = initials(displayName);
  const currentLabel = destinations.find((item) => item.key === active)?.label || 'Employés';
  const available = destinations.filter((item) => !item.permissions || item.permissions.some((permission) => hasPermission(permission)));
  const modalNavigation = compact && menuOpen;
  useBodyScrollLock(modalNavigation);

  useEffect(() => {
    setMenuOpen(false);
    setProfileOpen(false);
  }, [active]);

  useEffect(() => {
    const query = window.matchMedia('(max-width: 1100px)');
    const update = () => { setCompact(query.matches); setMenuOpen(false); };
    query.addEventListener('change', update);
    return () => query.removeEventListener('change', update);
  }, []);

  useEffect(() => {
    if (!modalNavigation) return undefined;
    const frame = window.requestAnimationFrame(() => sidebar.current?.querySelector('button')?.focus());
    const onKeyDown = (event) => {
      if (event.key === 'Escape') { event.preventDefault(); setMenuOpen(false); }
      if (event.key !== 'Tab') return;
      const controls = [...sidebar.current.querySelectorAll('a[href], button:not(:disabled)')];
      const first = controls[0];
      const last = controls.at(-1);
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    };
    document.addEventListener('keydown', onKeyDown);
    return () => {
      window.cancelAnimationFrame(frame);
      document.removeEventListener('keydown', onKeyDown);
      if (menuButton.current?.checkVisibility()) menuButton.current.focus();
    };
  }, [modalNavigation]);

  const openProfile = (event) => {
    event.preventDefault();
    if (!profileAvailable) return;
    setMenuOpen(false);
    setProfileOpen(true);
  };
  const logout = () => { clearSession(); navigate('/connexion', { replace: true }); };

  return <div className={`hr-app${modalNavigation ? ' navigation-open' : ''}`}>
    <a className="skip-link" href="#main-content">Aller au contenu</a>
    <header className="mobile-appbar" inert={modalNavigation}>
      <AppLink className="mobile-wordmark" href={homePath(user)} aria-label="Remonte RH, accueil" onClick={() => setMenuOpen(false)}>remonte<span>RH</span></AppLink>
      <span className="mobile-page-name">{currentLabel}</span>
      <ThemeToggle compact />
      <button ref={menuButton} className="icon-button navigation-toggle" type="button" aria-label="Ouvrir le menu" aria-expanded={modalNavigation} aria-controls="workspace-navigation" onClick={() => setMenuOpen(true)}><Menu size={20} aria-hidden="true" /></button>
    </header>
    <aside ref={sidebar} id="workspace-navigation" className="app-sidebar" role={modalNavigation ? 'dialog' : undefined} aria-modal={modalNavigation || undefined} aria-label={modalNavigation ? 'Menu Remonte RH' : 'Espace de travail'} inert={compact && !menuOpen}>
      <div className="sidebar-brand-row">
        <AppLink className="sidebar-brand" href={homePath(user)} aria-label="Remonte RH, accueil" onClick={() => setMenuOpen(false)}><span className="brand-monogram" aria-hidden="true">r<span>.</span></span><span><strong>remonte <b>RH</b></strong><small>Ressources humaines</small></span></AppLink>
        <button className="icon-button navigation-close" type="button" aria-label="Fermer le menu" onClick={() => setMenuOpen(false)}><X size={20} aria-hidden="true" /></button>
      </div>
      <nav className="sidebar-nav" aria-label="Navigation principale">
        {[false, true].map((personal) => {
          const items = available.filter((item) => Boolean(item.personal) === personal);
          if (!items.length) return null;
          return <div className="navigation-group" key={String(personal)}>
            <p className="sidebar-caption">{personal ? 'Mon espace' : 'Gestion RH'}</p>
            {items.map(({ key, label, icon: Icon }) => <AppLink key={key} className={`nav-item${active === key ? ' active' : ''}`} aria-current={active === key ? 'page' : undefined} href={pageRoutes[key].path} onClick={() => setMenuOpen(false)}><Icon size={18} strokeWidth={1.6} aria-hidden="true" /><span>{label}</span></AppLink>)}
          </div>;
        })}
      </nav>
      <div className="sidebar-bottom">
        <ThemeToggle />
        <div className="sidebar-user"><span className="user-avatar" aria-hidden="true">{badge}</span><span className="user-info"><strong>{displayName}</strong><a className="account-profile-link" href="#mon-profil" aria-disabled={!profileAvailable} aria-label={`Modifier mon profil : ${user.email || displayName}`} title={user.email} onClick={openProfile}>{user.email || 'Mon profil'}</a></span><button className="icon-button sidebar-logout" type="button" aria-label="Déconnexion" title="Déconnexion" onClick={logout}><LogOut size={18} strokeWidth={1.6} aria-hidden="true" /></button></div>
      </div>
    </aside>
    <main id="main-content" tabIndex={-1} className="app-main" inert={modalNavigation}>
      <div className="content-wrap">{children}<footer className="app-footer">Remonte RH <span>·</span> Gestion des ressources humaines</footer></div>
    </main>
    {profileOpen && <AccountProfile onClose={() => setProfileOpen(false)} onSaved={setUser} />}
  </div>;
}
