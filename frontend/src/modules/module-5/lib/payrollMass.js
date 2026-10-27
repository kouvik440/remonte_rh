export const analysisPath = '/api/analyses/masse-salariale/';
export const exportTypes = {
  csv: 'text/csv',
  xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  pdf: 'application/pdf',
};

export function initialFilters() {
  const now = new Date();
  return { start: `${now.getFullYear()}-01`, end: `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`, department: '', granularity: 'mensuelle' };
}

export function validateFilters(filters) {
  const errors = {};
  for (const key of ['start', 'end']) {
    if (!/^(?!0000)\d{4}-(0[1-9]|1[0-2])$/.test(filters[key])) errors[key] = 'Choisissez un mois entre les années 0001 et 9999.';
  }
  if (!errors.start && !errors.end && filters.start > filters.end) errors.end = 'La fin doit être égale ou postérieure au début.';
  return errors;
}

export function analysisQuery({ start, end, department }, extra = {}) {
  return new URLSearchParams({ periode_debut: start, periode_fin: end, ...(department ? { departement: department } : {}), ...extra }).toString();
}

export function massExportPath(filters, format) {
  return `${analysisPath}export/?${analysisQuery(filters, {
    format_fichier: format, granularite: filters.granularity,
  })}`;
}

export const money = (amount) => new Intl.NumberFormat('fr-FR', {
  style: 'currency', currency: 'XOF', minimumFractionDigits: 0, maximumFractionDigits: 2,
}).format(amount);

export function periodLabel(period) {
  if (!period.includes('-')) return period;
  const [year, month] = period.split('-');
  const date = new Date(0);
  date.setFullYear(Number(year), Number(month) - 1, 1);
  return new Intl.DateTimeFormat('fr-FR', { month: 'long', year: 'numeric' }).format(date);
}
