from django.db import migrations, models
import django.db.models.deletion


def copy_conge_requests_to_absences(apps, schema_editor):
    DemandeConge = apps.get_model("core", "DemandeConge")
    DemandeAbsence = apps.get_model("core", "DemandeAbsence")
    database = schema_editor.connection.alias

    for demande in DemandeConge.objects.using(database).select_related("type_conge"):
        absence = DemandeAbsence.objects.using(database).create(
            type_absence=demande.type_conge.libelle,
            date_debut=demande.date_debut,
            date_fin=demande.date_fin,
            motif=demande.motif,
            statut=demande.statut,
            employe_id=demande.employe_id,
            valideur_id=demande.valideur_id,
        )
        DemandeAbsence.objects.using(database).filter(pk=absence.pk).update(
            date_demande=demande.date_demande,
            date_validation=demande.date_validation,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0012_conge_module"),
    ]

    operations = [
        migrations.AddField(
            model_name="demandeabsence",
            name="valideur",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="absences_validees",
                to="core.employe",
            ),
        ),
        migrations.RunPython(
            copy_conge_requests_to_absences,
            migrations.RunPython.noop,
        ),
        migrations.DeleteModel(name="DemandeConge"),
    ]