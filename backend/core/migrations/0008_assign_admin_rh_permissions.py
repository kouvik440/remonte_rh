from django.db import migrations


def assign_admin_rh_permissions(apps, schema_editor):
    Role = apps.get_model("core", "Role")
    Permission = apps.get_model("auth", "Permission")
    database = schema_editor.connection.alias
    admin_role = Role.objects.using(database).filter(nom__iexact="ADMIN_RH").first()
    if admin_role is None:
        return

    role_permissions = Role.permissions.through
    permissions = Permission.objects.using(database).filter(
        content_type__app_label="core"
    )
    role_permissions.objects.using(database).bulk_create(
        [
            role_permissions(role_id=admin_role.pk, permission_id=permission.pk)
            for permission in permissions
        ],
        ignore_conflicts=True,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0007_move_role_permissions_to_auth"),
    ]

    operations = [
        migrations.RunPython(assign_admin_rh_permissions, migrations.RunPython.noop),
    ]