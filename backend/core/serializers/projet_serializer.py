from rest_framework import serializers

from core.models import AffectationProjet, Employe, Projet, TacheProjet


class ProjetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Projet
        fields = [
            "id",
            "code",
            "nom",
            "description",
            "date_debut",
            "date_fin",
            "actif",
        ]
        read_only_fields = ["code"]

    def validate(self, attrs):
        date_debut = attrs.get("date_debut")
        date_fin = attrs.get("date_fin")
        if self.instance:
            date_debut = attrs.get("date_debut", self.instance.date_debut)
            date_fin = attrs.get("date_fin", self.instance.date_fin)
        if date_debut and date_fin and date_fin < date_debut:
            raise serializers.ValidationError(
                {"date_fin": "La date de fin doit être égale ou postérieure au début."}
            )
        return attrs


class TacheProjetSerializer(serializers.ModelSerializer):
    class Meta:
        model = TacheProjet
        fields = ["id", "projet", "code", "nom", "description", "actif"]
        read_only_fields = ["projet", "code"]

    def validate(self, attrs):
        projet_id = self.context["projet_id"]
        nom = attrs.get("nom", self.instance.nom if self.instance else None)
        tasks = TacheProjet.objects.filter(projet_id=projet_id)
        if self.instance:
            tasks = tasks.exclude(pk=self.instance.pk)
        if nom and tasks.filter(nom=nom).exists():
            raise serializers.ValidationError(
                {"nom": "Ce nom est déjà utilisé dans ce projet."}
            )
        return attrs


class AffectationProjetSerializer(serializers.ModelSerializer):
    employe_matricule = serializers.CharField(source="employe.matricule", read_only=True)
    employe_nom = serializers.CharField(source="employe.nom", read_only=True)
    employe_prenom = serializers.CharField(source="employe.prenom", read_only=True)

    class Meta:
        model = AffectationProjet
        fields = [
            "id",
            "projet",
            "employe",
            "employe_matricule",
            "employe_nom",
            "employe_prenom",
            "date_affectation",
        ]
        read_only_fields = ["projet", "date_affectation"]


class AffectationEmployeRequestSerializer(serializers.Serializer):
    employe = serializers.PrimaryKeyRelatedField(queryset=Employe.objects.all())
