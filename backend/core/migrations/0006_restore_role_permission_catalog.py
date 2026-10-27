from django.db import migrations


RESOURCES = {
    "role": "Rôle",
    "permission": "Permission",
}

ACTIONS = {
    "read": "Consulter",
    "create": "Créer",
    "update": "Modifier",
    "delete": "Supprimer",
}

ASSIGN_PERMISSION = (
    "role.assign_permissions",
    "Attribuer des permissions à un rôle",
    "Ajouter ou retirer les permissions d'un rôle.",
)


def add_role_permission_catalog(apps, schema_editor):
    Permission = apps.get_model("core", "Permission")
    database = schema_editor.connection.alias

    for resource_code, resource_name in RESOURCES.items():
        for action_code, action_name in ACTIONS.items():
            Permission.objects.using(database).update_or_create(
                code=f"{resource_code}.{action_code}",
                defaults={
                    "nom": (
                        f"{action_name} {resource_name.lower()}s"
                        if action_code == "read"
                        else f"{action_name} {resource_name.lower()}"
                    ),
                    "description": (
                        f"{action_name} les données de {resource_name.lower()}."
                    ),
                },
            )

    Permission.objects.using(database).update_or_create(
        code=ASSIGN_PERMISSION[0],
        defaults={
            "nom": ASSIGN_PERMISSION[1],
            "description": ASSIGN_PERMISSION[2],
        },
    )


def remove_role_permission_catalog(apps, schema_editor):
    Permission = apps.get_model("core", "Permission")
    database = schema_editor.connection.alias
    codes = [
        f"{resource_code}.{action_code}"
        for resource_code in RESOURCES
        for action_code in ACTIONS
    ]
    codes.append(ASSIGN_PERMISSION[0])
    Permission.objects.using(database).filter(code__in=codes).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0005_alter_employe_managers_remove_employe_user_and_more"),
    ]

    operations = [
        migrations.RunPython(
            add_role_permission_catalog,
            remove_role_permission_catalog,
        ),
    ]