export const rulesPath = '/api/regles-paie/';
export const rateFields = [
  ['taux_cnss_salarial', 'CNSS salariale (%)'],
  ['taux_cnss_patronal', 'CNSS patronale (%)'],
  ['taux_tpa_patronal', 'TPA patronale (%)'],
  ['abattement_professionnel', 'Abattement professionnel (%)'],
  ['plafond_deduction_retraite', 'Plafond de déduction retraite (% de la base)'],
];
const percentage = (rate) => rate === undefined ? '' : String(Number((Number(rate) * 100).toFixed(4)));
const ratio = (value) => (Number(value) / 100).toFixed(6);

export function ruleForm(rule) {
  return {
    code: rule?.code || '', nom: rule?.nom || '', date_debut: rule?.date_debut || '', date_fin: rule?.date_fin || '',
    actif: rule?.actif ?? true, source_reference: rule?.source_reference || '',
    heures_mensuelles: rule?.heures_mensuelles || '', plafond_cnss: rule?.plafond_cnss || '',
    decimales_montant: String(rule?.decimales_montant ?? 0),
    ...Object.fromEntries(rateFields.map(([key]) => [key, percentage(rule?.[key])])),
    tranches_iuts: rule?.tranches_iuts?.map((row) => ({ ...row, maximum: row.maximum ?? '', taux: percentage(row.taux) })) || [{ minimum: '0', maximum: '', taux: '' }],
    reductions_iuts_charges: rule?.reductions_iuts_charges?.map((row) => ({ ...row, taux: percentage(row.taux) })) || [],
  };
}

export function rulePayload(form) {
  return {
    ...form, pays: 'BF', devise: 'XOF', jours_ouvres_semaine: 5,
    date_fin: form.date_fin || null, decimales_montant: Number(form.decimales_montant),
    ...Object.fromEntries(rateFields.map(([key]) => [key, ratio(form[key])])),
    tranches_iuts: form.tranches_iuts.map((row) => ({ ...row, maximum: row.maximum === '' ? null : row.maximum, taux: ratio(row.taux) })),
    reductions_iuts_charges: form.reductions_iuts_charges.map((row) => ({ charges: Number(row.charges), taux: ratio(row.taux) })),
  };
}
