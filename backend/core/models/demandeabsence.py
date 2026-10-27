from django.db import models
from .enums import StatutAbsence, StatutEmploye
from django.core.exceptions import ValidationError

class DemandeAbsence(models.Model):
    type_conge = models.ForeignKey(
        "core.TypeConge",
        on_delete=models.PROTECT,
        related_name="demandes_absence",
    )
    date_debut = models.DateField()
    date_fin = models.DateField()
    motif = models.TextField()
    statut = models.CharField(
        max_length=20,
        choices=StatutAbsence.choices,
        default=StatutAbsence.EN_ATTENTE,
    )
    date_demande = models.DateTimeField(auto_now_add=True)
    date_validation = models.DateTimeField(null=True, blank=True)
    valideur = models.ForeignKey(
        "core.Employe",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="absences_validees",
    )
    employe = models.ForeignKey(
        "core.Employe",
        on_delete=models.CASCADE,
        related_name="demandes_absence",
    )

    class Meta:
        ordering = ["-date_demande"]

    def clean(self):
        super().clean()
        if self.date_fin and self.date_debut and self.date_fin < self.date_debut:
            raise ValidationError(
                {"date_fin": "La date de fin doit etre apres ou egale a la date de debut."}
            )

    def __str__(self):
        return f"{self.employe} - {self.type_conge.libelle}"

