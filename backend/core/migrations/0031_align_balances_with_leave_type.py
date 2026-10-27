from django.db import migrations


def align_balances(apps, schema_editor):
    leave_types = apps.get_model("core", "TypeConge")
    balances = apps.get_model("core", "SoldeConge")
    database = schema_editor.connection.alias
    for leave_type in leave_types.objects.using(database).all().iterator():
        balances.objects.using(database).filter(type_conge_id=leave_type.pk).update(
            acquis=leave_type.jours_par_annee
        )


class Migration(migrations.Migration):
    dependencies = [("core", "0030_backfill_leave_balances_from_approved_requests")]
    operations = [migrations.RunPython(align_balances, migrations.RunPython.noop)]
