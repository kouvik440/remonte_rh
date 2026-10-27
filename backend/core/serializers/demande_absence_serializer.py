from rest_framework import serializers

from core.models import DemandeAbsence, TypeConge


class DemandeAbsenceSerializer(serializers.ModelSerializer):
    employe_nom = serializers.CharField(source="employe.nom", read_only=True)
    employe_prenom = serializers.CharField(source="employe.prenom", read_only=True)
    type_conge_code = serializers.CharField(source="type_conge.code", read_only=True)
    type_conge_libelle = serializers.CharField(source="type_conge.libelle", read_only=True)

    class Meta:
        model = DemandeAbsence
        fields = [
            "id",
            "type_conge",
            "type_conge_code",
            "type_conge_libelle",
            "date_debut",
            "date_fin",
            "motif",
            "statut",
            "date_demande",
            "date_validation",
            "valideur",
            "employe",
            "employe_nom",
            "employe_prenom",
        ]
        read_only_fields = ["statut", "date_demande", "date_validation", "valideur", "employe"]
        extra_kwargs = {"employe": {"required": False}}

    type_conge = serializers.PrimaryKeyRelatedField(
        queryset=TypeConge.objects.filter(actif=True),
        required=True,
    )

    def validate(self, attrs):
        date_debut = attrs.get(
            "date_debut",
            self.instance.date_debut if self.instance else None,
        )
        date_fin = attrs.get(
            "date_fin",
            self.instance.date_fin if self.instance else None,
        )
        if date_debut and date_fin and date_fin < date_debut:
            raise serializers.ValidationError(
                {"date_fin": "La date de fin doit etre apres ou egale a la date de debut."}
            )
        return attrs


class DemandeAbsenceDetailSerializer(DemandeAbsenceSerializer):
    employe_matricule = serializers.CharField(source="employe.matricule", read_only=True)
    departement_nom = serializers.CharField(
        source="employe.department.nom", read_only=True, default=None
    )
    valideur_nom = serializers.CharField(
        source="valideur.nom", read_only=True, default=None
    )
    valideur_prenom = serializers.CharField(
        source="valideur.prenom", read_only=True, default=None
    )

    class Meta(DemandeAbsenceSerializer.Meta):
        fields = DemandeAbsenceSerializer.Meta.fields + [
            "employe_matricule",
            "departement_nom",
            "valideur_nom",
            "valideur_prenom",
        ]


class PlanningEventQuerySerializer(serializers.Serializer):
    date_debut = serializers.DateField(required=True)
    date_fin = serializers.DateField(required=True)
    departement = serializers.IntegerField(required=False, min_value=1)
    employe = serializers.IntegerField(required=False, min_value=1)

    def validate(self, attrs):
        if attrs["date_fin"] < attrs["date_debut"]:
            raise serializers.ValidationError(
                {"date_fin": "La date de fin doit etre apres ou egale a la date de debut."}
            )
        return attrs


class PlanningEventSerializer(serializers.Serializer):
    id = serializers.CharField()
    type_evenement = serializers.ChoiceField(
        choices=["PRESENCE_PREVUE", "ABSENCE"]
    )
    demande_absence_id = serializers.IntegerField(allow_null=True)
    employe_id = serializers.IntegerField()
    employe_nom = serializers.CharField()
    employe_prenom = serializers.CharField()
    departement_id = serializers.IntegerField(allow_null=True)
    departement_nom = serializers.CharField(allow_null=True)
    type_conge_code = serializers.CharField(allow_null=True)
    type_conge_libelle = serializers.CharField(allow_null=True)
    date_debut = serializers.DateField()
    date_fin = serializers.DateField()
