from decimal import Decimal

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0027_projet_tacheprojet_affectationprojet"),
    ]

    operations = [
        migrations.AddField(
            model_name="contrat",
            name="heures_journalieres",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=4,
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(Decimal("0.01")),
                    django.core.validators.MaxValueValidator(Decimal("24.00")),
                ],
            ),
        ),
        migrations.AddConstraint(
            model_name="contrat",
            constraint=models.CheckConstraint(
                check=(
                    models.Q(heures_journalieres__isnull=True)
                    | models.Q(
                        heures_journalieres__gte=Decimal("0.01"),
                        heures_journalieres__lte=Decimal("24.00"),
                    )
                ),
                name="contrat_daily_hours_range",
            ),
        ),
        migrations.CreateModel(
            name="FeuilleTemps",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("semaine_debut", models.DateField()),
                (
                    "statut",
                    models.CharField(
                        choices=[
                            ("BROUILLON", "Brouillon"),
                            ("SOUMISE", "Soumise"),
                            ("VALIDEE", "Validee"),
                        ],
                        default="BROUILLON",
                        max_length=20,
                    ),
                ),
                (
                    "employe",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="feuilles_temps",
                        to="core.employe",
                    ),
                ),
            ],
            options={
                "ordering": ["-semaine_debut", "employe__nom", "employe__prenom"],
            },
        ),
        migrations.CreateModel(
            name="LigneFeuilleTemps",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date_travail", models.DateField()),
                (
                    "heures",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=5,
                        validators=[
                            django.core.validators.MinValueValidator(
                                Decimal("0.01")
                            ),
                            django.core.validators.MaxValueValidator(
                                Decimal("24.00")
                            ),
                        ],
                    ),
                ),
                ("commentaire", models.TextField(blank=True)),
                (
                    "feuille",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lignes",
                        to="core.feuilletemps",
                    ),
                ),
                (
                    "projet",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="lignes_temps",
                        to="core.projet",
                    ),
                ),
                (
                    "tache",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="lignes_temps",
                        to="core.tacheprojet",
                    ),
                ),
            ],
            options={
                "ordering": ["date_travail", "projet__nom", "tache__nom"],
            },
        ),
        migrations.AddConstraint(
            model_name="feuilletemps",
            constraint=models.UniqueConstraint(
                fields=("employe", "semaine_debut"),
                name="unique_timesheet_employee_week",
            ),
        ),
        migrations.AddConstraint(
            model_name="lignefeuilletemps",
            constraint=models.CheckConstraint(
                check=models.Q(
                    heures__gte=Decimal("0.01"),
                    heures__lte=Decimal("24.00"),
                ),
                name="timesheet_line_hours_range",
            ),
        ),
    ]