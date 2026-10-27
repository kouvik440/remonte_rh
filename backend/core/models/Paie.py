from django.db import models
from django.db.models import Q

from core.storage import PrivatePayrollStorage
from .enums import StatutPaie

class Paie(models.Model):
    periode = models.CharField(max_length=100)
    libelle = models.CharField(max_length=150)
    salaire_base = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    salaire_brut = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    salaire_net = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    cout_charge = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    cotisations = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    devise = models.CharField(max_length=3, default="XOF")
    detail_calcul = models.JSONField(default=dict, blank=True)
    bulletin_pdf = models.FileField(
        upload_to="bulletins/",
        storage=PrivatePayrollStorage(),
        null=True,
        blank=True,
    )
    statut = models.CharField(
        max_length=20,
        choices=StatutPaie.choices,
        default=StatutPaie.BROUILLON,
    )
    date_calcul = models.DateTimeField(null=True, blank=True)
    date_validation = models.DateTimeField(null=True, blank=True)
    date_paiement = models.DateTimeField(null=True, blank=True)
    date_annulation = models.DateTimeField(null=True, blank=True)
    motif_annulation = models.TextField(blank=True)
    employe = models.ForeignKey(
        "core.Employe",
        on_delete=models.CASCADE,
        related_name="paiements",
    )
    valideur = models.ForeignKey(
        "core.Employe",
        on_delete=models.SET_NULL,
        related_name="paies_validees",
        null=True,
        blank=True,
    )
    annule_par = models.ForeignKey(
        "core.Employe",
        on_delete=models.SET_NULL,
        related_name="paies_annulees",
        null=True,
        blank=True,
    )
    ordre_virement = models.ForeignKey(
        "core.OrdreVirement",
        on_delete=models.SET_NULL,
        related_name="paiements",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["date_calcul", "periode"]
        constraints = [
            models.UniqueConstraint(
                fields=["employe", "periode"],
                condition=~Q(statut="ANNULE"),
                name="unique_active_paie_employe_periode",
            )
        ]

    def __str__(self):
        return f"{self.libelle} - {self.employe}"


