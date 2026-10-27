export function homePath(user) {
  const permissions = Array.isArray(user?.permissions) ? user.permissions : [];
  const can = (code) => permissions.includes(code);
  if (can('employe.read')) return '/employes';
  if (can('feuille_temps.decide')) return '/feuilles-de-temps';
  if (can('paie.update') || can('ordre_virement.read')) return '/paie';
  if (can('paie.read')) return user.roles?.includes('FRONTEND_MODULE_6_TGM') ? '/tgm' : '/masse-salariale';
  if (can('demande_absence.update')) return '/conges';
  if (can('coordonnees_bancaires.manage')) return '/coordonnees-bancaires';
  return '/feuilles-de-temps';
}
