import re

from rest_framework import serializers

from core.models import ElementVariablePaie
from core.models.enums import NatureElementPaie


class ElementVariablePaieSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElementVariablePaie
        fields = [
            "id",
            "employe",
            "periode",
            "nature",
            "libelle",
            "montant",
            "quantite",
            "coefficient",
            "soumis_iuts",
            "soumis_cnss",
            "verse_en_especes",
            "valide",
            "date_creation",
        ]
        read_only_fields = ["date_creation", "valide"]
        extra_kwargs = {
            "montant": {"required": False, "allow_null": True},
            "quantite": {"required": False, "allow_null": True},
            "coefficient": {"required": False, "allow_null": True},
        }

    def validate_periode(self, value):
        if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", value):
            raise serializers.ValidationError("La période doit être au format AAAA-MM.")
        return value

    def validate(self, attrs):
        if "valide" in self.initial_data:
            raise serializers.ValidationError(
                {"valide": "Utilisez l'action dédiée pour valider cet élément."}
            )
        nature = attrs.get("nature", self.instance.nature if self.instance else None)
        montant = attrs.get("montant", self.instance.montant if self.instance else None)
        quantite = attrs.get("quantite", self.instance.quantite if self.instance else None)
        coefficient = attrs.get(
            "coefficient",
            self.instance.coefficient if self.instance else None,
        )
        soumis_iuts = attrs.get(
            "soumis_iuts",
            self.instance.soumis_iuts if self.instance else False,
        )
        soumis_cnss = attrs.get(
            "soumis_cnss",
            self.instance.soumis_cnss if self.instance else False,
        )

        if nature == NatureElementPaie.HEURE_SUP:
            if quantite is None or coefficient is None or quantite < 0 or coefficient <= 0:
                raise serializers.ValidationError(
                    {"quantite": "Les heures supplémentaires exigent une quantité et un coefficient positif."}
                )
            if montant is not None:
                raise serializers.ValidationError(
                    {"montant": "Le montant des heures supplémentaires est calculé depuis la base horaire."}
                )
        elif montant is None or montant < 0:
            raise serializers.ValidationError(
                {"montant": "Un montant positif ou nul est requis pour cet élément."}
            )

        if nature in (NatureElementPaie.RETENUE, NatureElementPaie.CHARGE_PATRONALE):
            if soumis_iuts or soumis_cnss:
                raise serializers.ValidationError(
                    "Une retenue ou charge patronale ne peut pas alimenter les assiettes salariales."
                )
        return attrs


class PaieCalculationRequestSerializer(serializers.Serializer):
    regle_paie = serializers.IntegerField(required=False, min_value=1)
    charges_familiales = serializers.IntegerField(
        required=False,
        default=0,
        min_value=0,
        max_value=4,
    )


class PaieAnnulationRequestSerializer(serializers.Serializer):
    motif = serializers.CharField(max_length=500)


class PaiePaiementRequestSerializer(serializers.Serializer):
    ordre_virement = serializers.IntegerField(min_value=1)


class ElementVariablePaieQuerySerializer(serializers.Serializer):
    employe = serializers.IntegerField(required=False, min_value=1)
    periode = serializers.CharField(required=False, max_length=7)

    def validate_periode(self, value):
        if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", value):
            raise serializers.ValidationError("La période doit être au format AAAA-MM.")
        return value