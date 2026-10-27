from django.db import migrations


def create_payroll_mass_role(apps, schema_editor):
    database = schema_editor.connection.alias
    roles = apps.get_model("core", "Role")
    permissions = apps.get_model("auth", "Permission")
    content_types = apps.get_model("contenttypes", "ContentType")
    role, _ = roles.objects.using(database).get_or_create(
        nom="FRONTEND_MODULE_5_MASSE_SALARIALE",
        defaults={"description": "Consultation de la masse salariale, ventilations et exports."},
    )
    for model in ("paie", "departement"):
        content_type, _ = content_types.objects.using(database).get_or_create(app_label="core", model=model)
        permission, _ = permissions.objects.using(database).get_or_create(
            content_type_id=content_type.pk, codename=f"view_{model}",
            defaults={"name": f"Can view {model}"},
        )
        roles.permissions.through.objects.using(database).get_or_create(role_id=role.pk, permission_id=permission.pk)


class Migration(migrations.Migration):
    dependencies = [("core", "0041_transfer_document_permission")]
    operations = [migrations.RunPython(create_payroll_mass_role, migrations.RunPython.noop)]
