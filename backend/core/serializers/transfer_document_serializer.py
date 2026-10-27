from django.utils import timezone
from rest_framework import serializers

from core.services.bank_rib import normalize_uemoa_rib


class TransferDocumentRequestSerializer(serializers.Serializer):
    coordonnees_bancaires = serializers.IntegerField(min_value=1)
    donneur_nom = serializers.CharField(max_length=200)
    donneur_adresse = serializers.CharField(max_length=500)
    donneur_telephone = serializers.CharField(max_length=30, required=False, allow_blank=True, default="")
    banque = serializers.CharField(max_length=100)
    agence = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    compte_debit = serializers.CharField(max_length=64)
    lieu = serializers.CharField(max_length=100)
    date_execution = serializers.DateField()
    motif = serializers.CharField(max_length=250)
    signataire = serializers.CharField(max_length=150)
    fonction_signataire = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    canal = serializers.ChoiceField(choices=["BANQUE", "INTERNE", "SICA", "RTGS"], default="BANQUE")

    def validate_compte_debit(self, value):
        try:
            rib = normalize_uemoa_rib(value)
        except ValueError as error:
            raise serializers.ValidationError(str(error)) from error
        if not rib.startswith("BF"):
            raise serializers.ValidationError("Le compte à débiter doit être domicilié au Burkina Faso (RIB BF).")
        return rib

    def validate_date_execution(self, value):
        if value < timezone.localdate():
            raise serializers.ValidationError("La date d’exécution ne peut pas être passée.")
        return value
