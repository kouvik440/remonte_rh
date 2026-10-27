from django.db import models


class Projet(models.Model):
    code = models.CharField(max_length=30, unique=True)
    nom = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    date_debut = models.DateField(null=True, blank=True)
    date_fin = models.DateField(null=True, blank=True)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ["nom"]
        permissions = [
            ("assign_employees", "Can assign employees to project"),
        ]

    def __str__(self):
        return f"{self.code} - {self.nom}"


class TacheProjet(models.Model):
    projet = models.ForeignKey(
        Projet,
        on_delete=models.CASCADE,
        related_name="taches",
    )
    code = models.CharField(max_length=30)
    nom = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ["projet__nom", "nom"]
        constraints = [
            models.UniqueConstraint(
                fields=["projet", "code"],
                name="unique_tache_projet_code",
            ),
            models.UniqueConstraint(
                fields=["projet", "nom"],
                name="unique_tache_projet_nom",
            ),
        ]

    def __str__(self):
        return f"{self.projet.code} - {self.nom}"


class AffectationProjet(models.Model):
    projet = models.ForeignKey(
        Projet,
        on_delete=models.CASCADE,
        related_name="affectations",
    )
    employe = models.ForeignKey(
        "core.Employe",
        on_delete=models.CASCADE,
        related_name="affectations_projet",
    )
    date_affectation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["employe__nom", "employe__prenom"]
        constraints = [
            models.UniqueConstraint(
                fields=["projet", "employe"],
                name="uniq_proj_emp_assign",
            )
        ]

    def __str__(self):
        return f"{self.employe} - {self.projet}"
