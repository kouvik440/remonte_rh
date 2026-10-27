from rest_framework import serializers

from core.models import TypeConge


class TypeCongeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeConge
        read_only_fields = ["id", "code", "date_creation"]
        fields = [
            "id",
            "code",
            "libelle",
            "jours_par_annee",
            "est_payant",
            "actif",
            "date_creation",
        ]


