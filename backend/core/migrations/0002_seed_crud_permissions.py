from django.db import migrations


PERMISSION_RESOURCES = {
    "departement": "Département",
    "poste": "Poste",
    "type_contrat": "Type de contrat",
    "type_document": "Type de document",
    "contrat": "Contrat",
    "contrat_type_contrat": "Association contrat-type",
    "coordonnees_bancaires": "Coordonnées bancaires",
    "demande_absence": "Demande d'absence",
    "document": "Document",
    "document_employe": "Document employé",
    "ordre_virement": "Ordre de virement",
    "paie": "Paie",
    "employe": "Employé",
    "role": "Rôle",
    "permission": "Permission",
}

PERMISSION_ACTIONS = {
    "read": "Consulter",
    "create": "Créer",
    "update": "Modifier",
    "delete": "Supprimer",
}


def create_crud_permissions(apps, schema_editor):
    Permission = apps.get_model("core", "Permission")

    for resource_code, resource_name in PERMISSION_RESOURCES.items():
        for action_code, action_name in PERMISSION_ACTIONS.items():
            Permission.objects.update_or_create(
                code=f"{resource_code}.{action_code}",
                defaults={
                    "nom": f"{action_name} {resource_name.lower()}s" if action_code == "read" else f"{action_name} {resource_name.lower()}",
                    "description": f"{action_name} les données de {resource_name.lower()}.",
                },
            )

    extra_permissions = [
        (
            "employe.assign_roles",
            "Attribuer des rôles à un employé",
            "Ajouter ou retirer les rôles d'un employé.",
        ),
        (
            "role.assign_permissions",
            "Attribuer des permissions à un rôle",
            "Ajouter ou retirer les permissions d'un rôle.",
        ),
    ]
    for code, name, description in extra_permissions:
        Permission.objects.update_or_create(
            code=code,
            defaults={"nom": name, "description": description},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_crud_permissions, migrations.RunPython.noop),
    ]