export function initialPeriod() {
  const now = new Date();
  return { start: `${now.getFullYear()}-01`, end: `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}` };
}

export function validatePeriod(period) {
  const errors = {};
  for (const field of ['start', 'end']) {
    if (!/^(?!0000)\d{4}-(0[1-9]|1[0-2])$/.test(period[field])) errors[field] = 'Choisissez un mois entre 0001 et 9999.';
  }
  if (!errors.start && !errors.end && period.start > period.end) errors.end = 'La fin doit être égale ou postérieure au début.';
  return errors;
}

export function reportPaths({ start, end, department, employee }) {
  const [year, month] = end.split('-').map(Number);
  const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const lastDay = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1];
  return {
    rates: `/api/analyses/tgm/?${new URLSearchParams({ periode_debut: start, periode_fin: end, ...(department ? { departement: department } : {}), ...(employee ? { employe: employee } : {}) })}`,
    costs: `/api/analyses/couts-projets/?${new URLSearchParams({ date_debut: `${start}-01`, date_fin: `${end}-${lastDay}` })}`,
  };
}

export function amount(value, currency = 'XOF') {
  if (value === null || value === undefined) return 'Indisponible';
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency, maximumFractionDigits: 2 }).format(value);
}
