from django.conf import settings
from django.db import models


class EmployeHistorique(models.Model):
    employe = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="historique_professionnel")
    categorie = models.CharField(max_length=20, choices=[("POSTE", "Poste"), ("CONTRAT", "Contrat"), ("RESPONSABLE", "Responsable")])
    objet_id = models.PositiveIntegerField(null=True, blank=True)
    operation = models.CharField(max_length=20, choices=[("INITIAL", "État initial"), ("CREATION", "Création"), ("MODIFICATION", "Modification"), ("SUPPRESSION", "Suppression")])
    avant = models.JSONField(default=dict, editable=False)
    apres = models.JSONField(default=dict, editable=False)
    date_evenement = models.DateTimeField(auto_now_add=True)
    auteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="changements_rh")
    auteur_nom = models.CharField(max_length=205, blank=True)

    class Meta:
        ordering = ["-date_evenement", "-pk"]
