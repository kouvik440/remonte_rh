from decimal import Decimal

from rest_framework import serializers


class CoutProjetQuerySerializer(serializers.Serializer):
    date_debut = serializers.DateField()
    date_fin = serializers.DateField()

    def validate(self, attrs):
        if attrs["date_fin"] < attrs["date_debut"]:
            raise serializers.ValidationError(
                {"date_fin": "La date de fin doit être égale ou postérieure au début."}
            )
        return attrs


class RentabiliteProjetQuerySerializer(CoutProjetQuerySerializer):
    projet = serializers.IntegerField(min_value=1)
    chiffre_affaires = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0"))
