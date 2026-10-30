export function employeeFullName(employee) {
  return `${employee.employe_prenom} ${employee.employe_nom}`.trim();
}

export function employeeAssignmentOption(employee) {
  return {
    employe: employee.id,
    employe_prenom: employee.prenom,
    employe_nom: employee.nom,
    employe_matricule: employee.matricule,
  };
}

export function matchesSearch(value, search) {
  return value.toLocaleLowerCase('fr').includes(search.trim().toLocaleLowerCase('fr'));
}
