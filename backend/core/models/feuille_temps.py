from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .enums import StatutFeuilleTemps


class FeuilleTemps(models.Model):
    employe = models.ForeignKey(
        "core.Employe",
        on_delete=models.CASCADE,
        related_name="feuilles_temps",
    )
    semaine_debut = models.DateField()
    statut = models.CharField(
        max_length=20,
        choices=StatutFeuilleTemps.choices,
        default=StatutFeuilleTemps.BROUILLON,
    )
    date_decision = models.DateTimeField(null=True, blank=True)
    motif_refus = models.TextField(blank=True, default="")
    valideur = models.ForeignKey(
        "core.Employe",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="feuilles_temps_validees",
    )

    class Meta:
        ordering = ["-semaine_debut", "employe__nom", "employe__prenom"]
        permissions = [
            ("decide", "Can decide submitted timesheets"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["employe", "semaine_debut"],
                name="unique_timesheet_employee_week",
            )
        ]

    def clean(self):
        super().clean()
        if self.semaine_debut and self.semaine_debut.weekday() != 0:
            raise ValidationError(
                {"semaine_debut": "La semaine doit commencer un lundi."}
            )

    def __str__(self):
        return f"{self.employe} - semaine du {self.semaine_debut}"


class LigneFeuilleTemps(models.Model):
    feuille = models.ForeignKey(
        FeuilleTemps,
        on_delete=models.CASCADE,
        related_name="lignes",
    )
    date_travail = models.DateField()
    projet = models.ForeignKey(
        "core.Projet",
        on_delete=models.PROTECT,
        related_name="lignes_temps",
    )
    tache = models.ForeignKey(
        "core.TacheProjet",
        on_delete=models.PROTECT,
        related_name="lignes_temps",
    )
    heures = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.01")),
            MaxValueValidator(Decimal("24.00")),
        ],
    )
    commentaire = models.TextField(blank=True)

    class Meta:
        ordering = ["date_travail", "projet__nom", "tache__nom"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(
                    heures__gte=Decimal("0.01"),
                    heures__lte=Decimal("24.00"),
                ),
                name="timesheet_line_hours_range",
            )
        ]

    def clean(self):
        super().clean()
        if self.feuille_id and self.date_travail:
            week_start = self.feuille.semaine_debut
            if week_start.weekday() != 0:
                raise ValidationError(
                    {"feuille": "La semaine de la feuille doit commencer un lundi."}
                )
            if not week_start <= self.date_travail <= week_start + timedelta(days=6):
                raise ValidationError(
                    {"date_travail": "La date doit appartenir à la semaine de la feuille."}
                )
        if self.projet_id and self.tache_id:
            if self.tache.projet_id != self.projet_id:
                raise ValidationError(
                    {"tache": "La tâche doit appartenir au projet indiqué."}
                )

    def __str__(self):
        return f"{self.feuille} - {self.date_travail} - {self.heures} h"