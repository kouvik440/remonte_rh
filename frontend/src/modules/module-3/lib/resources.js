import { hasPermission } from '../../../shared/lib/api.js';

export const resources = {
  bank: { title: 'Coordonnées bancaires', resource: 'coordonnees_bancaires', path: '/api/coordonnees-bancaires/' },
};

export const canAct = (kind, action) => Boolean(resources[kind]) && hasPermission(`${resources[kind].resource}.${action}`);

export function fieldsFor(kind, { employees }, editing) {
  const employeeOptions = employees.map((employee) => ({ value: employee.id, label: `${employee.prenom} ${employee.nom} · ${employee.matricule}` }));
  return [
    { name: 'banque', label: 'Banque', required: true, maxLength: 100 },
    { name: 'iban', label: 'RIB', required: true, maxLength: 34 },
    ...(!editing && hasPermission('coordonnees_bancaires.manage') ? [
      { name: 'employe', label: 'Employé', type: 'select', required: true, options: employeeOptions },
    ] : []),
  ];
}

export function formFor(fields, record) {
  return Object.fromEntries(fields.map((field) => [field.name,
    record?.[field.name] ?? (field.type === 'multiple' ? [] : field.type === 'checkbox' ? true : ''),
  ]));
}

export function payloadFor(fields, form) {
  return Object.fromEntries(fields.map((field) => [field.name,
    field.type === 'select' ? Number(form[field.name])
      : field.type === 'date' && !form[field.name] ? null : form[field.name],
  ]));
}
