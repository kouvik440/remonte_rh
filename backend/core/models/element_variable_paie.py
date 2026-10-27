from django.db import models

from .enums import NatureElementPaie


class ElementVariablePaie(models.Model):
    employe = models.ForeignKey(
        "core.Employe",
        on_delete=models.CASCADE,
        related_name="elements_variables_paie",
    )
    periode = models.CharField(max_length=7)
    nature = models.CharField(max_length=20, choices=NatureElementPaie.choices)
    libelle = models.CharField(max_length=150)
    montant = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    quantite = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        null=True,
        blank=True,
    )
    coefficient = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        null=True,
        blank=True,
    )
    soumis_iuts = models.BooleanField(default=False)
    soumis_cnss = models.BooleanField(default=False)
    verse_en_especes = models.BooleanField(default=True)
    valide = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["periode", "employe__nom", "employe__prenom", "id"]
        indexes = [models.Index(fields=["employe", "periode", "valide"])]

    def __str__(self):
        return f"{self.employe} - {self.periode} - {self.libelle}"