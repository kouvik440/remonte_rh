from django.db import migrations


def create_payroll_role(apps, schema_editor):
    database = schema_editor.connection.alias
    roles = apps.get_model("core", "Role")
    permissions = apps.get_model("auth", "Permission")
    content_types = apps.get_model("contenttypes", "ContentType")
    role, _ = roles.objects.using(database).get_or_create(
        nom="FRONTEND_MODULE_4_PAIE_VIREMENTS",
        defaults={"description": "Gestion des paies : brouillons, calcul, décisions et bulletins."},
    )
    for model, actions in (("paie", ("add", "view", "change", "delete")), ("employe", ("view",))):
        content_type, _ = content_types.objects.using(database).get_or_create(
            app_label="core", model=model,
        )
        for action in actions:
            permission, _ = permissions.objects.using(database).get_or_create(
                content_type_id=content_type.pk, codename=f"{action}_{model}",
                defaults={"name": f"Can {action} {model}"},
            )
            roles.permissions.through.objects.using(database).get_or_create(
                role_id=role.pk, permission_id=permission.pk,
            )


class Migration(migrations.Migration):
    dependencies = [("core", "0033_encrypt_bank_details")]
    operations = [migrations.RunPython(create_payroll_role, migrations.RunPython.noop)]
