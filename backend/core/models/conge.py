from django.db import models


class TypeConge(models.Model):
    code = models.CharField(max_length=20, unique=True)
    libelle = models.CharField(max_length=100)
    jours_par_annee = models.PositiveIntegerField(default=0, help_text="Droit annuel en jours")
    est_payant = models.BooleanField(default=True)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["code"]
        verbose_name = "Type de conge"
        verbose_name_plural = "Types de conge"

    def __str__(self):
        return f"{self.code} - {self.libelle}"


class SoldeConge(models.Model):
    employe = models.ForeignKey(
        "core.Employe",
        on_delete=models.CASCADE,
        related_name="soldes_conge",
    )
    type_conge = models.ForeignKey(
        TypeConge,
        on_delete=models.CASCADE,
        related_name="soldes",
        null=True,
        blank=True,
    )
    annee = models.PositiveIntegerField()
    acquis = models.PositiveIntegerField(default=0)
    pris = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("employe", "type_conge", "annee")
        ordering = ["employe", "type_conge", "annee"]
        verbose_name = "Solde de conge"
        verbose_name_plural = "Soldes de conge"

    @property
    def restant(self):
        return self.acquis - self.pris

    def __str__(self):
        return f"{self.employe} - {self.type_conge.code} - {self.annee} (restant: {self.restant})"
