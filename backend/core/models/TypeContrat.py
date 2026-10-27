from django.db import models
from .enums import StatutEmploye
class TypeContrat(models.Model):
    type = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "type_contrat_typecontrat"
        ordering = ["type"]

    def __str__(self):
        return self.type