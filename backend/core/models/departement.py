from django.db import models
class Departement(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return self.nom