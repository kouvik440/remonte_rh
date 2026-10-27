export const pageRoutes = {
  login: { path: '/connexion', title: 'Connexion' },
  employees: { path: '/employes', title: 'Employés', active: 'employees' },
  departments: { path: '/departements', title: 'Départements', active: 'departments' },
  roles: { path: '/roles', title: 'Rôles et accès', active: 'roles' },
  leaves: { path: '/conges', title: 'Congés et absences', active: 'leaves' },
  records: { path: '/coordonnees-bancaires', title: 'Coordonnées bancaires', active: 'records' },
  payroll: { path: '/paie', title: 'Paie et virements', active: 'payroll' },
  'my-payslips': { path: '/mes-bulletins', title: 'Mes bulletins de paie', active: 'my-payslips' },
  'payroll-mass': { path: '/masse-salariale', title: 'Masse salariale', active: 'payroll-mass' },
  tgm: { path: '/tgm', title: 'TGM et coûts projets', active: 'tgm' },
  timesheets: { path: '/feuilles-de-temps', title: 'Feuilles de temps', active: 'timesheets' },
};

const navigationEvent = 'remonte-rh:navigation';

export function routeKey(pathname) {
  const path = pathname.replace(/\/+$/, '') || '/';
  if (['/', '/index.html', '/pages/index.html'].includes(path)) return 'login';
  const route = Object.entries(pageRoutes).find(([, item]) => item.path === path);
  if (route) return route[0];
  const legacy = /^\/pages\/([^/]+)\.html$/.exec(path);
  return legacy && Object.hasOwn(pageRoutes, legacy[1]) ? legacy[1] : null;
}

export const getLocation = () => window.location.pathname + window.location.search + window.location.hash;

export function subscribeToNavigation(listener) {
  window.addEventListener('popstate', listener);
  window.addEventListener(navigationEvent, listener);
  return () => {
    window.removeEventListener('popstate', listener);
    window.removeEventListener(navigationEvent, listener);
  };
}

export function navigate(destination, { replace = false } = {}) {
  const url = new URL(destination, window.location.href);
  const key = routeKey(url.pathname);
  if (url.origin !== window.location.origin || !key) {
    window.location[replace ? 'replace' : 'assign'](url.href);
    return;
  }
  const path = pageRoutes[key].path + url.search + url.hash;
  if (path === getLocation()) return;
  window.history[replace ? 'replaceState' : 'pushState'](null, '', path);
  window.dispatchEvent(new Event(navigationEvent));
}
