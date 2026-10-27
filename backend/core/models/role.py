from django.contrib.auth.models import Permission
from django.db import models


class Role(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(
        Permission,
        related_name="roles",
        blank=True,
    )

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return self.nom