from django.db import migrations


def retire_previous_demo_rules(apps, schema_editor):
    rules = apps.get_model("core", "ReglePaie")
    # Demo rates cannot become validated payroll rules merely by removing a flag.
    rules.objects.using(schema_editor.connection.alias).filter(est_fictif=True).update(
        actif=False, valide=False,
    )


class Migration(migrations.Migration):
    dependencies = [("core", "0034_frontend_payroll_role")]
    operations = [
        migrations.RunPython(retire_previous_demo_rules),
        migrations.RemoveField(model_name="reglepaie", name="est_fictif"),
    ]
