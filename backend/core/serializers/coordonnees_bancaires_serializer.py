from rest_framework import serializers

from core.models import CoordonneesBancaires


class CoordonneesBancairesSerializer(serializers.ModelSerializer):
    employe_nom = serializers.CharField(source="employe.nom", read_only=True)
    employe_prenom = serializers.CharField(source="employe.prenom", read_only=True)
    class Meta:
        model = CoordonneesBancaires
        fields = [
            "id",
            "iban",
            "bic",
            "swift",
            "banque",
            "date_modification",
            "employe",
            "employe_nom",
            "employe_prenom",
        ]
        extra_kwargs = {"employe": {"required": False}}
