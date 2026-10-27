from django.db import migrations


def extend_module_profiles(apps, schema_editor):
    database = schema_editor.connection.alias
    roles = apps.get_model("core", "Role")
    permissions = apps.get_model("auth", "Permission")
    types = apps.get_model("contenttypes", "ContentType")
    module_one = [("employe", action) for action in ("add_employe", "view_employe", "change_employe", "delete_employe", "assign_roles")]
    module_one += [("role", action) for action in ("add_role", "view_role", "change_role", "delete_role", "view_permission")]
    module_one += [("departement", "view_departement"), ("typecontrat", "view_typecontrat")]
    module_one += [("contrat", f"{action}_contrat") for action in ("add", "view", "change", "delete")]
    module_four = [("paie", f"{action}_paie") for action in ("add", "view", "change", "delete")]
    module_four += [("ordrevirement", f"{action}_ordrevirement") for action in ("add", "view", "change", "delete")]
    module_four += [("employe", "view_employe")]
    for name, entries in (("FRONTEND_MODULE_1_EMPLOYES_ACCES", module_one), ("FRONTEND_MODULE_4_PAIE_VIREMENTS", module_four)):
        role, _ = roles.objects.using(database).get_or_create(nom=name)
        for model, codename in entries:
            content_type, _ = types.objects.using(database).get_or_create(app_label="core", model=model)
            permission, _ = permissions.objects.using(database).get_or_create(
                content_type_id=content_type.pk, codename=codename, defaults={"name": f"Can {codename}"},
            )
            roles.permissions.through.objects.using(database).get_or_create(role_id=role.pk, permission_id=permission.pk)


class Migration(migrations.Migration):
    dependencies = [("core", "0036_transfer_decision_audit")]
    operations = [migrations.RunPython(extend_module_profiles, migrations.RunPython.noop)]
