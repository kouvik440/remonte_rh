from django.db import migrations


def add_contract_type_management(apps, schema_editor):
    database = schema_editor.connection.alias
    roles = apps.get_model("core", "Role")
    permissions = apps.get_model("auth", "Permission")
    types = apps.get_model("contenttypes", "ContentType")
    role = roles.objects.using(database).get(nom="FRONTEND_MODULE_1_EMPLOYES_ACCES")
    content_type, _ = types.objects.using(database).get_or_create(app_label="core", model="typecontrat")
    for action in ("add", "view", "change", "delete"):
        permission, _ = permissions.objects.using(database).get_or_create(
            content_type_id=content_type.pk, codename=f"{action}_typecontrat",
            defaults={"name": f"Can {action} contract type"},
        )
        roles.permissions.through.objects.using(database).get_or_create(role_id=role.pk, permission_id=permission.pk)


class Migration(migrations.Migration):
    dependencies = [("core", "0038_protect_contract_types")]
    operations = [migrations.RunPython(add_contract_type_management, migrations.RunPython.noop)]
