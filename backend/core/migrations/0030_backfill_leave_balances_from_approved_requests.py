from collections import defaultdict
from datetime import date, timedelta

from django.db import migrations


def backfill_missing_leave_balances(apps, schema_editor):
    DemandeAbsence = apps.get_model("core", "DemandeAbsence")
    SoldeConge = apps.get_model("core", "SoldeConge")
    TypeConge = apps.get_model("core", "TypeConge")
    database = schema_editor.connection.alias
    used_dates = defaultdict(set)

    approved = DemandeAbsence.objects.using(database).filter(statut="VALIDEE")
    for absence in approved.only(
        "employe_id",
        "type_conge_id",
        "date_debut",
        "date_fin",
    ).iterator():
        for year in range(absence.date_debut.year, absence.date_fin.year + 1):
            year_start = date(year, 1, 1)
            year_end = date(year, 12, 31)
            current = max(absence.date_debut, year_start)
            end = min(absence.date_fin, year_end)
            while current <= end:
                if current.weekday() < 5:
                    used_dates[(absence.employe_id, absence.type_conge_id, year)].add(current)
                current += timedelta(days=1)

    for (employee_id, type_id, year), dates in used_dates.items():
        if SoldeConge.objects.using(database).filter(
            employe_id=employee_id,
            type_conge_id=type_id,
            annee=year,
        ).exists():
            continue

        leave_type = TypeConge.objects.using(database).get(pk=type_id)
        if leave_type.jours_par_annee <= 0:
            continue

        SoldeConge.objects.using(database).create(
            employe_id=employee_id,
            type_conge_id=type_id,
            annee=year,
            acquis=leave_type.jours_par_annee,
            pris=len(dates),
        )


class Migration(migrations.Migration):
    dependencies = [("core", "0029_feuille_temps_decision")]

    operations = [
        migrations.RunPython(
            backfill_missing_leave_balances,
            migrations.RunPython.noop,
        ),
    ]
