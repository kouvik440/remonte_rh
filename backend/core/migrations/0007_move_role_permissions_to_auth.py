from django.db import migrations, models


RESOURCE_MODEL_NAMES = {
    "contrat": "contrat",
    "contrat_type_contrat": "contrattypecontrat",
    "coordonnees_bancaires": "coordonneesbancaires",
    "demande_absence": "demandeabsence",
    "departement": "departement",
    "document": "document",
    "document_employe": "documentemploye",
    "employe": "employe",
    "ordre_virement": "ordrevirement",
    "paie": "paie",
    "permission": "role",
    "poste": "poste",
    "role": "role",
    "type_contrat": "typecontrat",
    "type_document": "typedocument",
}

ACTION_PREFIXES = {
    "create": "add",
    "read": "view",
    "update": "change",
    "delete": "delete",
}


def _permission_identity(code):
    try:
        resource_name, action = code.rsplit(".", 1)
        model_name = RESOURCE_MODEL_NAMES[resource_name]
    except (KeyError, ValueError) as error:
        raise RuntimeError(f"Unsupported legacy permission code: {code}") from error

    if action in ACTION_PREFIXES:
        suffix = "permission" if resource_name == "permission" else model_name
        codename = f"{ACTION_PREFIXES[action]}_{suffix}"
    else:
        codename = action
    return model_name, codename


def move_role_permissions(apps, schema_editor):
    LegacyPermission = apps.get_model("core", "Permission")
    Role = apps.get_model("core", "Role")
    ContentType = apps.get_model("contenttypes", "ContentType")
    AuthPermission = apps.get_model("auth", "Permission")
    database = schema_editor.connection.alias

    for legacy_permission in LegacyPermission.objects.using(database).all():
        model_name, codename = _permission_identity(legacy_permission.code)
        model = apps.get_model("core", model_name)
        content_type, _ = ContentType.objects.using(database).get_or_create(
            app_label="core",
            model=model_name,
        )
        action = codename.split("_", 1)[0]
        auth_permission, _ = AuthPermission.objects.using(database).get_or_create(
            content_type_id=content_type.pk,
            codename=codename,
            defaults={
                "name": (
                    f"Can {action} permission"
                    if legacy_permission.code.startswith("permission.")
                    else str(legacy_permission.nom)
                ),
            },
        )

        linked_roles = Role.objects.using(database).filter(
            permissions__pk=legacy_permission.pk
        )
        for role in linked_roles.iterator():
            role.auth_permissions.add(auth_permission)


def prevent_reverse(apps, schema_editor):
    raise migrations.IrreversibleError(
        "The custom permission catalog was removed; this migration cannot be reversed."
    )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0006_restore_role_permission_catalog"),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="role",
            name="auth_permissions",
            field=models.ManyToManyField(
                blank=True,
                related_name="roles",
                to="auth.permission",
            ),
        ),
        migrations.RunPython(move_role_permissions, prevent_reverse),
        migrations.RemoveField(
            model_name="role",
            name="permissions",
        ),
        migrations.RenameField(
            model_name="role",
            old_name="auth_permissions",
            new_name="permissions",
        ),
        migrations.DeleteModel(
            name="Permission",
        ),
    ]