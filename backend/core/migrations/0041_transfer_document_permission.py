from django.db import migrations


def create_document_permission(apps, schema_editor):
    database = schema_editor.connection.alias
    types = apps.get_model("contenttypes", "ContentType")
    permissions = apps.get_model("auth", "Permission")
    roles = apps.get_model("core", "Role")
    content_type, _ = types.objects.using(database).get_or_create(app_label="core", model="ordrevirement")
    permission, _ = permissions.objects.using(database).get_or_create(
        content_type_id=content_type.pk, codename="generate_document",
        defaults={"name": "Can prepare and download bank transfer documents"},
    )
    for role in roles.objects.using(database).filter(nom__in=["ADMIN_RH", "FRONTEND_MODULE_4_PAIE_VIREMENTS"]):
        roles.permissions.through.objects.using(database).get_or_create(role_id=role.pk, permission_id=permission.pk)


class Migration(migrations.Migration):
    dependencies = [("core", "0040_transfer_order_document")]
    operations = [migrations.RunPython(create_document_permission, migrations.RunPython.noop)]
