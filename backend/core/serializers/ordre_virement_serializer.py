import re
from django.utils import timezone
from rest_framework import serializers

from core.models import OrdreVirement


class OrdreVirementSerializer(serializers.ModelSerializer):
    document_disponible = serializers.SerializerMethodField()
    date_generation = serializers.DateTimeField(required=False, default=serializers.CreateOnlyDefault(timezone.now))
    employe_nom = serializers.CharField(source="employe.nom", read_only=True)
    employe_prenom = serializers.CharField(source="employe.prenom", read_only=True)
    employe_matricule = serializers.CharField(source="employe.matricule", read_only=True)
    decideur_nom = serializers.CharField(source="decideur.nom", read_only=True, default="")
    decideur_prenom = serializers.CharField(source="decideur.prenom", read_only=True, default="")
    class Meta:
        model = OrdreVirement
        fields = [
            "id",
            "periode",
            "statut",
            "date_generation",
            "date_traitement",
            "employe",
            "employe_nom", "employe_prenom", "employe_matricule",
            "date_decision", "motif_decision", "decideur", "decideur_nom", "decideur_prenom",
            "document_disponible", "document_genere_le", "document_genere_par",
        ]
        read_only_fields = ["statut", "date_traitement", "date_decision", "motif_decision", "decideur", "document_genere_le", "document_genere_par"]

    def get_document_disponible(self, obj):
        return bool(obj.document_pdf)

    def validate_periode(self, value):
        if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", value):
            raise serializers.ValidationError("La période doit être au format AAAA-MM.")
        return value

    def validate(self, attrs):
        if self.initial_data.get("date_traitement") is not None:
            raise serializers.ValidationError(
                {"date_traitement": "La date de traitement est définie par l'action dédiée."}
            )
        if self.instance and "statut" in self.initial_data:
            raise serializers.ValidationError(
                {"statut": "Le statut est géré par les actions dédiées."}
            )
        if not self.instance and attrs.get("statut", "GENERE") != "GENERE":
            raise serializers.ValidationError(
                {"statut": "Un ordre doit être créé avec le statut GENERE."}
            )
        return attrs


class OrdreVirementMotifSerializer(serializers.Serializer):
    motif = serializers.CharField(max_length=500, required=False, allow_blank=True)
