from django.db import migrations


def remove_legacy_permissions(apps, schema_editor):
    Permission = apps.get_model("core", "Permission")
    Permission.objects.filter(code__in=("rh.manage", "employe.view")).delete()


def restore_legacy_permissions(apps, schema_editor):
    Permission = apps.get_model("core", "Permission")
    Permission.objects.update_or_create(
        code="rh.manage",
        defaults={"nom": "Gérer les RH", "description": "Administration RH"},
    )
    Permission.objects.update_or_create(
        code="employe.view",
        defaults={"nom": "Voir les employés", "description": "Accès lecture employés"},
    )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_keep_employee_crud_permissions"),
    ]

    operations = [
        migrations.RunPython(remove_legacy_permissions, restore_legacy_permissions),
    ]