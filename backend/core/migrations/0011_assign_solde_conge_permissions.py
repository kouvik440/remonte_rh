from django.db import migrations


def assign_solde_conge_permissions(apps, schema_editor):
    Role = apps.get_model("core", "Role")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    database = schema_editor.connection.alias
    content_type, _ = ContentType.objects.using(database).get_or_create(
        app_label="core",
        model="soldeconge",
    )

    admin_role = Role.objects.using(database).filter(nom__iexact="ADMIN_RH").first()
    if admin_role is None:
        return

    role_permissions = Role.permissions.through
    action_prefixes = {
        "read": "view",
        "create": "add",
        "update": "change",
        "delete": "delete",
    }
    for action, prefix in action_prefixes.items():
        codename = f"{prefix}_soldeconge"
        permission, _ = Permission.objects.using(database).get_or_create(
            content_type_id=content_type.pk,
            codename=codename,
            defaults={"name": f"Can {action} leave balance"},
        )
        role_permissions.objects.using(database).get_or_create(
            role_id=admin_role.pk,
            permission_id=permission.pk,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0010_soldeconge_and_more"),
    ]

    operations = [
        migrations.RunPython(
            assign_solde_conge_permissions,
            migrations.RunPython.noop,
        ),
    ]