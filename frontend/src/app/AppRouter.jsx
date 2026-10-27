import React, { Component, lazy, Suspense, useEffect, useSyncExternalStore } from 'react';
import AppLayout from '../shared/components/AppLayout.jsx';
import PageLoading from '../shared/components/PageLoading.jsx';
import AppLink from '../shared/components/AppLink.jsx';
import { clearSession, getUser } from '../shared/lib/api.js';
import { homePath } from '../shared/lib/homePath.js';
import { getLocation, navigate, pageRoutes, routeKey, subscribeToNavigation } from '../shared/lib/navigation.js';

const pages = {
  'login': lazy(() => import('../modules/module-1/pages/LoginPage.jsx')),
  'employees': lazy(() => import('../modules/module-1/pages/EmployeesPage.jsx')),
  'departments': lazy(() => import('../modules/module-1/pages/DepartmentsPage.jsx')),
  'roles': lazy(() => import('../modules/module-1/pages/RolesPage.jsx')),
  'leaves': lazy(() => import('../modules/module-2/pages/LeavePage.jsx')),
  'records': lazy(() => import('../modules/module-3/pages/EmployeeRecordsPage.jsx')),
  'payroll': lazy(() => import('../modules/module-4/pages/PayrollPage.jsx')),
  'my-payslips': lazy(() => import('../modules/module-4/pages/MyPayslipsPage.jsx')),
  'payroll-mass': lazy(() => import('../modules/module-5/pages/PayrollMassPage.jsx')),
  'tgm': lazy(() => import('../modules/module-6/pages/TgmPage.jsx')),
  'timesheets': lazy(() => import('../modules/module-7/pages/TimesheetsPage.jsx')),
};

class RouteErrorBoundary extends Component {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() {
    return this.state.failed ? <div className="message-box error" role="alert">
      <p>Impossible d’afficher cette page. Rechargez-la pour réessayer.</p>
      <button type="button" className="outline-button" onClick={() => window.location.reload()}>Recharger la page</button>
    </div> : this.props.children;
  }
}

function RouteFocus() {
  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      window.scrollTo(0, 0);
      const heading = document.querySelector('#main-content h1, .login-heading h2, .route-not-found h1');
      heading?.setAttribute('tabindex', '-1');
      heading?.focus({ preventScroll: true });
    });
    return () => window.cancelAnimationFrame(frame);
  }, []);
  return null;
}

function AuthenticatedPage({ active, children }) {
  const authenticated = Boolean(localStorage.getItem('access_token'));
  const validPermissions = Array.isArray(getUser().permissions);
  useEffect(() => {
    if (authenticated && validPermissions) return;
    clearSession();
    navigate(`/connexion${authenticated ? '?session=permissions' : ''}`, { replace: true });
  }, [authenticated, validPermissions]);
  return authenticated && validPermissions ? <AppLayout active={active}>{children}</AppLayout> : null;
}

export default function AppRouter() {
  const location = useSyncExternalStore(subscribeToNavigation, getLocation);
  const key = routeKey(window.location.pathname);
  const route = pageRoutes[key];
  const Page = pages[key];
  useEffect(() => {
    if (route && getLocation() === location && window.location.pathname !== route.path) {
      navigate(route.path + window.location.search + window.location.hash, { replace: true });
    }
  }, [location, route]);
  useEffect(() => {
    document.title = `${route?.title || 'Page introuvable'} — Remonte RH`;
    document.body.classList.toggle('hr-app-body', Boolean(route?.active));
  }, [route]);
  if (!route) return <main className="content-wrap route-not-found">
    <h1>Page introuvable</h1><p>Cette adresse ne correspond à aucune page de l’application.</p>
    <AppLink href={localStorage.getItem('access_token') ? homePath(getUser()) : '/connexion'}>Revenir à l’accueil</AppLink>
    <RouteFocus key={location} />
  </main>;
  const content = <RouteErrorBoundary key={location}>
    <Suspense fallback={<PageLoading />}><Page /><RouteFocus /></Suspense>
  </RouteErrorBoundary>;
  return route.active ? <AuthenticatedPage active={route.active}>{content}</AuthenticatedPage> : content;
}
