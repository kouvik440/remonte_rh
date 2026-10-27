from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .enums import StatutContrat


class Contrat(models.Model):
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)
    salaire_base = models.DecimalField(max_digits=12, decimal_places=2)
    heures_journalieres = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(Decimal("0.01")),
            MaxValueValidator(Decimal("24.00")),
        ],
    )
    statut = models.CharField(
        max_length=20,
        choices=StatutContrat.choices,
        default=StatutContrat.EN_COURS,
    )
    employe = models.ForeignKey(
        "core.Employe",
        on_delete=models.CASCADE,
        related_name="contrats",
    )
    poste = models.ForeignKey("core.Poste", on_delete=models.PROTECT, null=True, blank=True, related_name="contrats")
    type = models.ManyToManyField(
        "core.TypeContrat",
        through="ContratTypeContrat",
        related_name="contrats",
    )

    class Meta:
        db_table = "contrat_contrat"
        ordering = ["date_debut"]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(heures_journalieres__isnull=True)
                    | models.Q(
                        heures_journalieres__gte=Decimal("0.01"),
                        heures_journalieres__lte=Decimal("24.00"),
                    )
                ),
                name="contrat_daily_hours_range",
            )
        ]

    def __str__(self):
        return f"{self.employe} - {self.date_debut}"
