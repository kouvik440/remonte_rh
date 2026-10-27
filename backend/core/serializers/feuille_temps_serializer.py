from decimal import Decimal

from rest_framework import serializers

from core.models import FeuilleTemps, LigneFeuilleTemps, Projet, TacheProjet


class LigneFeuilleTempsInputSerializer(serializers.Serializer):
    date_travail = serializers.DateField()
    projet = serializers.PrimaryKeyRelatedField(queryset=Projet.objects.all())
    tache = serializers.PrimaryKeyRelatedField(queryset=TacheProjet.objects.all())
    heures = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=Decimal("0.01"),
        max_value=Decimal("24.00"),
        required=False,
    )
    jours = serializers.DecimalField(max_digits=3, decimal_places=2, min_value=Decimal("0.01"), max_value=Decimal("1"), required=False)
    commentaire = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if ("heures" in attrs) == ("jours" in attrs):
            raise serializers.ValidationError("Renseignez soit les heures, soit les jours, pour chaque ligne.")
        return attrs


class FeuilleTempsWriteSerializer(serializers.Serializer):
    semaine_debut = serializers.DateField()
    lignes = LigneFeuilleTempsInputSerializer(many=True)

    def validate_semaine_debut(self, value):
        if value.weekday() != 0:
            raise serializers.ValidationError("La semaine doit commencer un lundi.")
        if self.instance and value != self.instance.semaine_debut:
            raise serializers.ValidationError(
                "La semaine d'une feuille existante ne peut pas être modifiée."
            )
        return value


class LigneFeuilleTempsSerializer(serializers.ModelSerializer):
    projet_code = serializers.CharField(source="projet.code", read_only=True)
    projet_nom = serializers.CharField(source="projet.nom", read_only=True)
    tache_code = serializers.CharField(source="tache.code", read_only=True)
    tache_nom = serializers.CharField(source="tache.nom", read_only=True)

    class Meta:
        model = LigneFeuilleTemps
        fields = [
            "id",
            "date_travail",
            "projet",
            "projet_code",
            "projet_nom",
            "tache",
            "tache_code",
            "tache_nom",
            "heures",
            "commentaire",
        ]


class FeuilleTempsSerializer(serializers.ModelSerializer):
    employe = serializers.IntegerField(source="employe_id", read_only=True)
    employe_nom = serializers.CharField(source="employe.nom", read_only=True)
    employe_prenom = serializers.CharField(source="employe.prenom", read_only=True)
    employe_matricule = serializers.CharField(source="employe.matricule", read_only=True)
    total_heures = serializers.SerializerMethodField()
    jours_saisis = serializers.SerializerMethodField()
    valideur_nom = serializers.CharField(source="valideur.nom", read_only=True, default="")
    valideur_prenom = serializers.CharField(source="valideur.prenom", read_only=True, default="")
    lignes = LigneFeuilleTempsSerializer(many=True, read_only=True)

    def get_total_heures(self, sheet):
        return str(sum((line.heures for line in sheet.lignes.all()), Decimal("0.00")))

    def get_jours_saisis(self, sheet):
        return len({line.date_travail for line in sheet.lignes.all()})

    class Meta:
        model = FeuilleTemps
        fields = [
            "id",
            "employe",
            "employe_nom",
            "employe_prenom",
            "employe_matricule",
            "total_heures",
            "jours_saisis",
            "semaine_debut",
            "statut",
            "valideur",
            "valideur_nom",
            "valideur_prenom",
            "date_decision",
            "motif_refus",
            "lignes",
        ]
        read_only_fields = [
            "id",
            "employe",
            "employe_nom",
            "employe_prenom",
            "semaine_debut",
            "statut",
            "valideur",
            "date_decision",
            "motif_refus",
            "lignes",
        ]

class FeuilleTempsRefusSerializer(serializers.Serializer):
    motif = serializers.CharField(
        allow_blank=False,
        trim_whitespace=True,
        max_length=2000,
    )

    def validate_motif(self, value):
        if not value:
            raise serializers.ValidationError("Le motif du refus est obligatoire.")
        return value


class FeuilleTempsTaskOptionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    code = serializers.CharField()
    nom = serializers.CharField()


class FeuilleTempsProjectQuerySerializer(serializers.Serializer):
    a_saisir = serializers.BooleanField(default=False)


class FeuilleTempsProjectOptionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    code = serializers.CharField()
    nom = serializers.CharField()
    taches = FeuilleTempsTaskOptionSerializer(many=True, read_only=True)


class FeuilleTempsQuerySerializer(serializers.Serializer):
    semaine_debut = serializers.DateField(required=False)
    date_travail = serializers.DateField(required=False)

    def validate_semaine_debut(self, value):
        if value.weekday() != 0:
            raise serializers.ValidationError("La semaine doit commencer un lundi.")
        return value
