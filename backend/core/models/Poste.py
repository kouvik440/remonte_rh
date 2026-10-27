from django.db import models 
from django.db.models.functions import Lower
class Poste(models.Model):
    nom = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["nom"]
        constraints = [models.UniqueConstraint(Lower("nom"), name="unique_position_name_case_insensitive")]

    def __str__(self):
        return self.nom
