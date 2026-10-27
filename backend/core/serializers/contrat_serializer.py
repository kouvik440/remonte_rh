from decimal import Decimal

from rest_framework import serializers

from core.models import Contrat, TypeContrat


class ContratSerializer(serializers.ModelSerializer):
    poste_nom = serializers.CharField(source="poste.nom", read_only=True, default="")
    types_libelles = serializers.SlugRelatedField(source="type", slug_field="type", many=True, read_only=True)
    salaire_base = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0"))
    heures_journalieres = serializers.DecimalField(
        max_digits=4,
        decimal_places=2,
        required=True,
        allow_null=False,
        min_value=Decimal("0.01"),
        max_value=Decimal("24.00"),
    )
    type = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=TypeContrat.objects,
        required=False,
    )

    class Meta:
        model = Contrat
        fields = [
            "id",
            "date_debut",
            "date_fin",
            "salaire_base",
            "heures_journalieres",
            "statut",
            "employe",
            "poste", "poste_nom",
            "type",
            "types_libelles",
        ]

    def validate(self, attrs):
        start = attrs.get("date_debut", self.instance.date_debut if self.instance else None)
        end = attrs.get("date_fin", self.instance.date_fin if self.instance else None)
        if start and end and end < start:
            raise serializers.ValidationError({"date_fin": "La fin doit être postérieure ou égale au début."})
        return attrs


class ContratQuerySerializer(serializers.Serializer):
    employe = serializers.IntegerField(required=False, min_value=1)
