from django.db import migrations


def assign_type_conge_permissions(apps, schema_editor):
    Role = apps.get_model("core", "Role")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    database = schema_editor.connection.alias
    content_type, _ = ContentType.objects.using(database).get_or_create(
        app_label="core",
        model="typeconge",
    )
    admin_role = Role.objects.using(database).filter(nom__iexact="ADMIN_RH").first()
    if admin_role is None:
        return

    role_permissions = Role.permissions.through
    for action, prefix in {
        "read": "view",
        "create": "add",
        "update": "change",
        "delete": "delete",
    }.items():
        permission, _ = Permission.objects.using(database).get_or_create(
            content_type_id=content_type.pk,
            codename=f"{prefix}_typeconge",
            defaults={"name": f"Can {action} leave type"},
        )
        role_permissions.objects.using(database).get_or_create(
            role_id=admin_role.pk,
            permission_id=permission.pk,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0013_consolidate_absence_requests"),
    ]

    operations = [
        migrations.RunPython(
            assign_type_conge_permissions,
            migrations.RunPython.noop,
        ),
    ]