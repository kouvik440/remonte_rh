from django.db import models


class StatutEmploye(models.TextChoices): 
    ACTIF = 'ACTIF', 'Actif'
    INACTIF = 'INACTIF', 'Inactif'
    SUSPENDU = 'SUSPENDU', 'Suspendu'


class StatutContrat(models.TextChoices): 
    EN_COURS = 'EN_COURS', 'En cours'
    CLOS = 'CLOS', 'Clos'
    RESILIE = 'RESILIE', 'Résilié'


class StatutAbsence(models.TextChoices): 
    EN_ATTENTE = 'EN_ATTENTE', 'En attente'
    VALIDEE = 'VALIDEE', 'Validée'
    REFUSEE = 'REFUSEE', 'Refusée'
    ANNULEE = 'ANNULEE', 'Annulée'


class StatutVirement(models.TextChoices):
    GENERE = 'GENERE', 'Généré'
    TRAITE = 'TRAITE', 'Traité'
    REJETE = 'REJETE', 'Rejeté'
    ANNULE = 'ANNULE', 'Annulé'


class StatutPaie(models.TextChoices):
    BROUILLON = 'BROUILLON', 'Brouillon'
    CALCULE = 'CALCULE', 'Calculé'
    VALIDEE = 'VALIDEE', 'Validée'
    PAYE = 'PAYE', 'Payé'
    ANNULE = 'ANNULE', 'Annulé'


class NatureElementPaie(models.TextChoices):
    PRIME = 'PRIME', 'Prime'
    HEURE_SUP = 'HEURE_SUP', 'Heures supplémentaires'
    AVANTAGE = 'AVANTAGE', 'Avantage en nature'
    RETENUE = 'RETENUE', 'Retenue salariale'
    CHARGE_PATRONALE = 'CHARGE_PATRONALE', 'Charge patronale'


class StatutFeuilleTemps(models.TextChoices):
    BROUILLON = 'BROUILLON', 'Brouillon'
    SOUMISE = 'SOUMISE', 'Soumise'
    VALIDEE = 'VALIDEE', 'Validee'
