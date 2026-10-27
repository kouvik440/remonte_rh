export const payrollPath = '/api/paiements/';
export const payrollStatuses = {
  BROUILLON: 'Brouillon', CALCULE: 'Calculée', VALIDEE: 'Validée', PAYE: 'Payée', ANNULE: 'Annulée',
};

export const employeeName = (payroll) => [payroll.employe_prenom, payroll.employe_nom].filter(Boolean).join(' ') || `Employé #${payroll.employe}`;
export const currentPeriod = () => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
};
export const money = (value, currency = 'XOF') => value === null || value === undefined
  ? 'Non calculé'
  : new Intl.NumberFormat('fr-FR', { style: 'currency', currency }).format(Number(value));
export const dateTime = (value) => value ? new Intl.DateTimeFormat('fr-FR', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) : 'Non renseignée';
export const ruleLabel = (rule) => `${rule.nom} · ${rule.valide ? 'Profil validé' : 'À valider'}`;

export function availableActions(payroll, permissions) {
  const actions = [];
  if (permissions.update) {
    if (payroll.statut === 'BROUILLON') actions.push('edit', 'calculate');
    if (payroll.statut === 'CALCULE') actions.push('validate');
    if (['BROUILLON', 'CALCULE', 'VALIDEE'].includes(payroll.statut)) actions.push('cancel');
    if (payroll.bulletin_generable && !payroll.bulletin_disponible) actions.push('generate');
  }
  if (permissions.delete && payroll.statut === 'BROUILLON') actions.push('delete');
  if (payroll.bulletin_disponible) actions.push('download');
  return actions;
}

export const actionLabels = {
  edit: 'Modifier', calculate: 'Calculer', validate: 'Valider', cancel: 'Annuler la paie',
  generate: 'Générer le bulletin', delete: 'Supprimer', download: 'Télécharger le bulletin',
};
