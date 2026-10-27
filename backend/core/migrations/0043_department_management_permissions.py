from django.db import migrations


def add_department_management(apps, schema_editor):
    database = schema_editor.connection.alias
    roles = apps.get_model("core", "Role")
    permissions = apps.get_model("auth", "Permission")
    content_types = apps.get_model("contenttypes", "ContentType")
    content_type, _ = content_types.objects.using(database).get_or_create(
        app_label="core", model="departement"
    )
    managers = roles.objects.using(database).filter(
        nom__in=("ADMIN_RH", "FRONTEND_MODULE_1_EMPLOYES_ACCES")
    )
    for action in ("add", "view", "change", "delete"):
        permission, _ = permissions.objects.using(database).get_or_create(
            content_type_id=content_type.pk,
            codename=f"{action}_departement",
            defaults={"name": f"Can {action} departement"},
        )
        for role in managers:
            roles.permissions.through.objects.using(database).get_or_create(
                role_id=role.pk, permission_id=permission.pk
            )


class Migration(migrations.Migration):
    dependencies = [("core", "0042_frontend_payroll_mass_role")]
    operations = [migrations.RunPython(add_department_management, migrations.RunPython.noop)]
