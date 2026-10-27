from django.db import migrations


def create_document_manage(apps, schema_editor):
    database = schema_editor.connection.alias
    content_type, _ = apps.get_model("contenttypes", "ContentType").objects.using(database).get_or_create(
        app_label="core", model="document"
    )
    permission, _ = apps.get_model("auth", "Permission").objects.using(database).get_or_create(
        content_type_id=content_type.pk, codename="manage",
        defaults={"name": "Can manage all employee document references"},
    )
    roles = apps.get_model("core", "Role")
    admin = roles.objects.using(database).filter(nom__iexact="ADMIN_RH").first()
    if admin:
        roles.permissions.through.objects.using(database).get_or_create(role_id=admin.pk, permission_id=permission.pk)


class Migration(migrations.Migration):
    dependencies = [("core", "0031_align_balances_with_leave_type")]
    operations = [migrations.RunPython(create_document_manage, migrations.RunPython.noop)]
