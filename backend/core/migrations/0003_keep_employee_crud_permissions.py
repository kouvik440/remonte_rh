from django.db import migrations


RESOURCE_CODES = (
    "departement",
    "poste",
    "type_contrat",
    "type_document",
    "contrat",
    "contrat_type_contrat",
    "coordonnees_bancaires",
    "demande_absence",
    "document",
    "document_employe",
    "ordre_virement",
    "paie",
    "role",
    "permission",
)
ACTION_CODES = ("read", "create", "update", "delete")


def remove_other_permissions(apps, schema_editor):
    Permission = apps.get_model("core", "Permission")
    codes = [
        f"{resource}.{action}"
        for resource in RESOURCE_CODES
        for action in ACTION_CODES
    ]
    codes.extend(("employe.assign_roles", "role.assign_permissions"))
    Permission.objects.filter(code__in=codes).delete()


def restore_other_permissions(apps, schema_editor):
    Permission = apps.get_model("core", "Permission")
    resources = {
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
        "role": "Rôle",
        "permission": "Permission",
    }
    actions = {
        "read": "Consulter",
        "create": "Créer",
        "update": "Modifier",
        "delete": "Supprimer",
    }

    for resource_code, resource_name in resources.items():
        for action_code, action_name in actions.items():
            name = (
                f"{action_name} {resource_name.lower()}s"
                if action_code == "read"
                else f"{action_name} {resource_name.lower()}"
            )
            Permission.objects.update_or_create(
                code=f"{resource_code}.{action_code}",
                defaults={
                    "nom": name,
                    "description": f"{action_name} les données de {resource_name.lower()}.",
                },
            )

    Permission.objects.update_or_create(
        code="employe.assign_roles",
        defaults={
            "nom": "Attribuer des rôles à un employé",
            "description": "Ajouter ou retirer les rôles d'un employé.",
        },
    )
    Permission.objects.update_or_create(
        code="role.assign_permissions",
        defaults={
            "nom": "Attribuer des permissions à un rôle",
            "description": "Ajouter ou retirer les permissions d'un rôle.",
        },
    )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_seed_crud_permissions"),
    ]

    operations = [
        migrations.RunPython(remove_other_permissions, restore_other_permissions),
    ]