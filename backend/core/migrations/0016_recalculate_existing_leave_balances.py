from datetime import date, timedelta

from django.db import migrations


def recalculate_existing_balances(apps, schema_editor):
    DemandeAbsence = apps.get_model("core", "DemandeAbsence")
    SoldeConge = apps.get_model("core", "SoldeConge")
    database = schema_editor.connection.alias

    for balance in SoldeConge.objects.using(database).exclude(type_conge_id=None):
        year_start = date(balance.annee, 1, 1)
        year_end = date(balance.annee, 12, 31)
        absences = DemandeAbsence.objects.using(database).filter(
            employe_id=balance.employe_id,
            type_conge_id=balance.type_conge_id,
            statut="VALIDEE",
            date_debut__lte=year_end,
            date_fin__gte=year_start,
        ).only("date_debut", "date_fin")

        working_dates = set()
        for absence in absences:
            current_date = max(absence.date_debut, year_start)
            end_date = min(absence.date_fin, year_end)
            while current_date <= end_date:
                if current_date.weekday() < 5:
                    working_dates.add(current_date)
                current_date += timedelta(days=1)

        SoldeConge.objects.using(database).filter(pk=balance.pk).update(
            pris=len(working_dates)
        )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0015_link_absence_to_leave_type"),
    ]

    operations = [
        migrations.RunPython(
            recalculate_existing_balances,
            migrations.RunPython.noop,
        ),
    ]