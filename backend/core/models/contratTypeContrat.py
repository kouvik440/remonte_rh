from django.db import models

from core.models.contrat import Contrat
from .enums import StatutEmploye

class ContratTypeContrat(models.Model):
    contrat = models.ForeignKey(Contrat, on_delete=models.CASCADE)
    type_contrat = models.ForeignKey(
        "core.TypeContrat",
        on_delete=models.PROTECT,
    )

    class Meta:
        db_table = "contrat_contrattypecontrat"
        unique_together = ("contrat", "type_contrat")

    def __str__(self):
        return f"{self.contrat} - {self.type_contrat}"
    
