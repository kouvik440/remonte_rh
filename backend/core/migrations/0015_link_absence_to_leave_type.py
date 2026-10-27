import re

from django.db import migrations, models
import django.db.models.deletion


def link_existing_absences_to_leave_types(apps, schema_editor):
    DemandeAbsence = apps.get_model("core", "DemandeAbsence")
    TypeConge = apps.get_model("core", "TypeConge")
    database = schema_editor.connection.alias

    for absence in DemandeAbsence.objects.using(database).all().iterator():
        label = (absence.type_absence or "Autre").strip() or "Autre"
        leave_type = TypeConge.objects.using(database).filter(
            libelle__iexact=label
        ).first()
        if leave_type is None:
            base_code = re.sub(r"[^A-Z0-9]+", "_", label.upper()).strip("_")[:20]
            base_code = base_code or "AUTRE"
            code = base_code
            suffix = 1
            while TypeConge.objects.using(database).filter(code=code).exists():
                suffix_text = f"_{suffix}"
                code = f"{base_code[:20 - len(suffix_text)]}{suffix_text}"
                suffix += 1
            leave_type = TypeConge.objects.using(database).create(
                code=code,
                libelle=label,
                jours_par_annee=0,
                est_payant=True,
                actif=True,
            )
        DemandeAbsence.objects.using(database).filter(pk=absence.pk).update(
            type_conge_id=leave_type.pk
        )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0014_assign_type_conge_permissions"),
    ]

    operations = [
        migrations.AddField(
            model_name="demandeabsence",
            name="type_conge",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="demandes_absence",
                to="core.typeconge",
            ),
        ),
        migrations.RunPython(
            link_existing_absences_to_leave_types,
            migrations.RunPython.noop,
        ),
        migrations.RemoveField(
            model_name="demandeabsence",
            name="type_absence",
        ),
        migrations.AlterField(
            model_name="demandeabsence",
            name="type_conge",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="demandes_absence",
                to="core.typeconge",
            ),
        ),
    ]