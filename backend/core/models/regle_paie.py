from django.core.exceptions import ValidationError
from django.db import models


class ReglePaie(models.Model):
    code = models.CharField(max_length=50, unique=True)
    nom = models.CharField(max_length=150)
    pays = models.CharField(max_length=2, default="BF")
    devise = models.CharField(max_length=3, default="XOF")
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)
    actif = models.BooleanField(default=True)
    heures_mensuelles = models.DecimalField(max_digits=7, decimal_places=2)
    decimales_montant = models.PositiveSmallIntegerField(default=0)
    jours_ouvres_semaine = models.PositiveSmallIntegerField(default=5)
    plafond_cnss = models.DecimalField(max_digits=12, decimal_places=2)
    taux_cnss_salarial = models.DecimalField(max_digits=7, decimal_places=6)
    taux_cnss_patronal = models.DecimalField(max_digits=7, decimal_places=6)
    taux_tpa_patronal = models.DecimalField(max_digits=7, decimal_places=6)
    abattement_professionnel = models.DecimalField(max_digits=7, decimal_places=6)
    plafond_deduction_retraite = models.DecimalField(max_digits=7, decimal_places=6)
    tranches_iuts = models.JSONField(default=list)
    reductions_iuts_charges = models.JSONField(default=list)
    source_reference = models.CharField(max_length=500, blank=True)
    valide = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_debut", "code"]

    def clean(self):
        super().clean()
        if self.date_fin and self.date_fin < self.date_debut:
            raise ValidationError({"date_fin": "La fin doit suivre le début d'effet."})
        if not 1 <= self.jours_ouvres_semaine <= 7:
            raise ValidationError({"jours_ouvres_semaine": "Valeur attendue entre 1 et 7."})
        if self.decimales_montant > 2:
            raise ValidationError({"decimales_montant": "Maximum deux décimales."})
        for field in (
            "taux_cnss_salarial",
            "taux_cnss_patronal",
            "taux_tpa_patronal",
            "abattement_professionnel",
            "plafond_deduction_retraite",
        ):
            value = getattr(self, field)
            if value is not None and not 0 <= value <= 1:
                raise ValidationError({field: "Le taux doit être compris entre 0 et 1."})

    def __str__(self):
        return f"{self.code} - {self.nom}"
