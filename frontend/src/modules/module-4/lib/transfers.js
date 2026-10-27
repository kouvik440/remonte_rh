export const transfersPath = '/api/ordres-virement/';
export const transferStatuses = { GENERE: 'Généré', TRAITE: 'Traité', REJETE: 'Rejeté', ANNULE: 'Annulé' };
export const transferLabels = { edit: 'Modifier l’ordre', traiter: 'Traiter', rejeter: 'Rejeter', annuler: 'Annuler l’ordre', delete: 'Supprimer l’ordre', reconcile: 'Marquer la paie payée', document: 'Générer l’ordre PDF', download_document: 'Télécharger l’ordre PDF' };
export const matchesPayroll = (order, payroll) => String(order.employe) === String(payroll.employe) && order.periode === payroll.periode;

export function eligiblePayrolls(payrolls, orders, editingOrder = null) {
  return payrolls.filter((payroll) => payroll.statut === 'VALIDEE' && !payroll.ordre_virement
    && !orders.some((order) => String(order.id) !== String(editingOrder?.id) && matchesPayroll(order, payroll) && ['GENERE', 'TRAITE'].includes(order.statut)));
}

export function reconcilablePayrolls(order, payrolls) {
  if (order.statut !== 'TRAITE' || !order.date_traitement) return [];
  if (payrolls.some((payroll) => String(payroll.ordre_virement) === String(order.id))) return [];
  return payrolls.filter((payroll) => payroll.statut === 'VALIDEE' && !payroll.ordre_virement && matchesPayroll(order, payroll));
}

export function transferActions(order, permissions, payrolls) {
  const actions = [];
  if (order.statut === 'GENERE') {
    if (permissions.update) {
      if (permissions.payrollRead && !order.document_disponible) actions.push('edit');
      actions.push('traiter', 'rejeter', 'annuler');
    }
    if (permissions.delete && !order.document_disponible) actions.push('delete');
  }
  if (permissions.document) {
    if (order.document_disponible) actions.push('download_document');
    else if (order.statut === 'GENERE') actions.push('document');
  }
  if (permissions.payrollRead && permissions.payrollUpdate && reconcilablePayrolls(order, payrolls).length) actions.push('reconcile');
  return actions;
}
