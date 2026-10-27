export const sheetPath = '/api/feuilles-temps/';
export const statusLabels = { BROUILLON: 'Brouillon', SOUMISE: 'Soumise', VALIDEE: 'Validée' };

export function dateValue(date) {
  return `${String(date.getFullYear()).padStart(4, '0')}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

export function parseDate(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
  const [year, month, day] = value.split('-').map(Number);
  const date = new Date(0);
  date.setFullYear(year, month - 1, day); date.setHours(12, 0, 0, 0);
  return year > 0 && dateValue(date) === value ? date : null;
}

export function currentMonday() {
  const now = new Date();
  now.setDate(now.getDate() - (now.getDay() + 6) % 7);
  return dateValue(now);
}

export function weekEnd(start) {
  const date = parseDate(start);
  if (!date) return '';
  date.setDate(date.getDate() + 6);
  return dateValue(date);
}

export function validateSheet(week, lines, projects) {
  const errors = {};
  const start = parseDate(week);
  if (!start || start.getDay() !== 1 || weekEnd(week).length !== 10) errors.week = 'Choisissez le lundi de la semaine.';
  lines.forEach((line, index) => {
    const prefix = `line-${index}-`;
    if (!parseDate(line.date) || line.date < week || line.date > weekEnd(week)) errors[`${prefix}date`] = 'Choisissez une date dans cette semaine.';
    const project = projects.find((item) => String(item.id) === line.project);
    if (!project) errors[`${prefix}project`] = 'Choisissez un projet auquel vous êtes affecté.';
    if (!project?.taches.some((item) => String(item.id) === line.task)) errors[`${prefix}task`] = 'Choisissez une tâche active du projet.';
    const quantity = line.quantity.trim().replace(',', '.');
    if (!/^\d{1,2}(\.\d{1,2})?$/.test(quantity) || Number(quantity) <= 0 || Number(quantity) > (line.unit === 'jours' ? 1 : 24)) {
      errors[`${prefix}quantity`] = line.unit === 'jours' ? 'Saisissez entre 0,01 et 1 jour.' : 'Saisissez entre 0,01 et 24 heures.';
    }
  });
  return errors;
}

export function sheetPayload(week, lines) {
  return { semaine_debut: week, lignes: lines.map((line) => ({ date_travail: line.date, projet: Number(line.project), tache: Number(line.task),
    [line.unit]: line.quantity.trim().replace(',', '.'), commentaire: line.comment.trim() })) };
}

const errorLabels = { semaine_debut: 'Semaine', date_travail: 'Date travaillée', lignes: 'Lignes', heures: 'Heures', jours: 'Jours', projet: 'Projet', tache: 'Tâche', employe: 'Employé', commentaire: 'Commentaire', motif: 'Motif', statut: 'Statut', code: 'Code', nom: 'Nom' };
export function readableError(value) {
  if (typeof value === 'string') return value;
  if (Array.isArray(value)) return value.map((item, index) => {
    const message = readableError(item);
    if (!message) return '';
    return typeof item === 'object' && !Array.isArray(item) ? `Ligne ${index + 1} : ${message}` : message;
  }).filter(Boolean).join(' ');
  if (!value || typeof value !== 'object') return '';
  return Object.entries(value).map(([key, item]) => `${['detail', 'non_field_errors'].includes(key) ? '' : `${errorLabels[key] || key} : `}${readableError(item)}`).join(' ');
}

export const currency = (value) => value === null || value === undefined ? 'Indisponible' : new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'XOF', maximumFractionDigits: 2 }).format(value);
