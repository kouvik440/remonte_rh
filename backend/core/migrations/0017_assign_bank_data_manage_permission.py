from django.db import migrations


def assign_bank_data_manage_permission(apps, schema_editor):
    Role = apps.get_model("core", "Role")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    database = schema_editor.connection.alias
    content_type, _ = ContentType.objects.using(database).get_or_create(
        app_label="core",
        model="coordonneesbancaires",
    )
    permission, _ = Permission.objects.using(database).get_or_create(
        content_type_id=content_type.pk,
        codename="manage",
        defaults={"name": "Can manage all bank details"},
    )
    admin_role = Role.objects.using(database).filter(nom__iexact="ADMIN_RH").first()
    if admin_role is not None:
        role_permissions = Role.permissions.through
        role_permissions.objects.using(database).get_or_create(
            role_id=admin_role.pk,
            permission_id=permission.pk,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0016_recalculate_existing_leave_balances"),
    ]

    operations = [
        migrations.RunPython(
            assign_bank_data_manage_permission,
            migrations.RunPython.noop,
        ),
    ]