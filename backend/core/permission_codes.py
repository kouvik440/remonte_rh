from django.contrib.auth.models import Permission


RESOURCE_MODEL_NAMES = {
    "conge": "typeconge",
    "contrat": "contrat",
    "contrat_type_contrat": "contrattypecontrat",
    "coordonnees_bancaires": "coordonneesbancaires",
    "demande_absence": "demandeabsence",
    "departement": "departement",
    "document": "document",
    "document_employe": "documentemploye",
    "employe": "employe",
    "feuille_temps": "feuilletemps",
    "ordre_virement": "ordrevirement",
    "paie": "paie",
    "permission": "role",
    "poste": "poste",
    "projet": "projet",
    "role": "role",
    "solde_conge": "soldeconge",
    "type_contrat": "typecontrat",
    "type_document": "typedocument",
    "tache": "tacheprojet",
}

CORE_PERMISSION_MODELS = frozenset(RESOURCE_MODEL_NAMES.values())
ACTION_PREFIXES = {
    "create": "add",
    "read": "view",
    "update": "change",
    "delete": "delete",
}
PREFIX_ACTIONS = {prefix: action for action, prefix in ACTION_PREFIXES.items()}
MODEL_RESOURCE_NAMES = {
    model_name: resource_name
    for resource_name, model_name in RESOURCE_MODEL_NAMES.items()
    if resource_name != "permission"
}


def permission_identity(code: str) -> tuple[str, str]:
    try:
        resource_name, action = code.rsplit(".", 1)
        resource_name = {"contract": "contrat"}.get(resource_name, resource_name)
        model_name = RESOURCE_MODEL_NAMES[resource_name]
    except (KeyError, ValueError) as error:
        raise ValueError("Code de permission invalide.") from error

    if action in ACTION_PREFIXES:
        suffix = "permission" if resource_name == "permission" else model_name
        codename = f"{ACTION_PREFIXES[action]}_{suffix}"
    else:
        codename = action
    return model_name, codename


def permission_code(permission: Permission) -> str:
    content_type = permission.content_type
    codename = permission.codename
    if content_type.app_label != "core":
        return f"{content_type.app_label}.{content_type.model}.{codename}"

    model_name = content_type.model
    if model_name == "role" and codename == "assign_permissions":
        return "role.assign_permissions"
    if model_name == "projet" and codename == "assign_employees":
        return "projet.assign_employees"

    for prefix, action in PREFIX_ACTIONS.items():
        prefix_value = f"{prefix}_"
        if not codename.startswith(prefix_value):
            continue

        suffix = codename[len(prefix_value):]
        if model_name == "role" and suffix == "permission":
            return f"permission.{action}"
        if suffix == model_name:
            resource_name = MODEL_RESOURCE_NAMES.get(model_name, model_name)
            return f"{resource_name}.{action}"

    resource_name = MODEL_RESOURCE_NAMES.get(model_name, model_name)
    return f"{resource_name}.{codename}"


def get_permission_by_code(code: str) -> Permission:
    model_name, codename = permission_identity(code)
    return Permission.objects.get(
        content_type__app_label="core",
        content_type__model=model_name,
        codename=codename,
    )
