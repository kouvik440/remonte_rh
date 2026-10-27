from django.db import migrations


def create_special_permission_codes(apps, schema_editor):
    Role = apps.get_model("core", "Role")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    database = schema_editor.connection.alias

    for model_name, codename, name in (
        ("employe", "assign_roles", "Can assign roles to employee"),
        ("role", "assign_permissions", "Can assign permissions to role"),
    ):
        content_type = ContentType.objects.using(database).get(
            app_label="core",
            model=model_name,
        )
        permission, _ = Permission.objects.using(database).get_or_create(
            content_type_id=content_type.pk,
            codename=codename,
            defaults={"name": name},
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
        ("core", "0008_assign_admin_rh_permissions"),
    ]

    operations = [
        migrations.RunPython(
            create_special_permission_codes,
            migrations.RunPython.noop,
        ),
    ]