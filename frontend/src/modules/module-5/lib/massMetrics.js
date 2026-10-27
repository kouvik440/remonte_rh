export const massColumns = [
  { key: 'paies_validees', label: 'Paies validées' },
  { key: 'brut_valide', label: 'Brut validé', amount: true },
  { key: 'net_valide', label: 'Net validé', amount: true },
  { key: 'cotisations_validees', label: 'Cotisations validées', amount: true },
  { key: 'cout_employeur_valide', label: 'Coût employeur validé', amount: true },
  { key: 'paies_payees', label: 'Paies payées' },
  { key: 'brut_paye', label: 'Brut payé', amount: true },
  { key: 'net_paye', label: 'Net payé', amount: true },
  { key: 'cotisations_payees', label: 'Cotisations payées', amount: true },
  { key: 'cout_employeur_paye', label: 'Coût employeur payé', amount: true },
];

export const evolutionMetrics = [
  { title: 'Salaires nets', validatedKey: 'net_valide', paidKey: 'net_paye' },
  { title: 'Coût employeur', validatedKey: 'cout_employeur_valide', paidKey: 'cout_employeur_paye' },
  { title: 'Cotisations', validatedKey: 'cotisations_validees', paidKey: 'cotisations_payees' },
];
