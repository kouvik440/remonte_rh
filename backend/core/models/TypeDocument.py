from django.db import models
from .enums import StatutEmploye
class TypeDocument(models.Model):
    code = models.CharField(max_length=50, unique=True)
    libelle = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["libelle"]

    def __str__(self):
        return self.libelle