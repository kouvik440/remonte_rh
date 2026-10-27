from django.db import migrations


def allow_task_deletion(apps, schema_editor):
    database = schema_editor.connection.alias
    Role = apps.get_model("core", "Role")
    Permission = apps.get_model("auth", "Permission")
    permission = Permission.objects.using(database).get(
        content_type__app_label="core", content_type__model="tacheprojet", codename="delete_tacheprojet"
    )
    role = Role.objects.using(database).filter(nom="FRONTEND_MODULE_7_FEUILLES_TEMPS").first()
    if role:
        Role.permissions.through.objects.using(database).get_or_create(role_id=role.pk, permission_id=permission.pk)


class Migration(migrations.Migration):
    dependencies = [("core", "0044_remaining_module_and_employee_roles")]
    operations = [migrations.RunPython(allow_task_deletion, migrations.RunPython.noop)]
