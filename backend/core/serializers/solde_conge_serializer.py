from rest_framework import serializers



class SoldeCongeSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, allow_null=True)
    employe = serializers.IntegerField()
    employe_nom = serializers.CharField(read_only=True)
    employe_prenom = serializers.CharField(read_only=True)
    employe_matricule = serializers.CharField(read_only=True)
    type_conge = serializers.IntegerField()
    type_conge_libelle = serializers.CharField()
    type_conge_code = serializers.CharField()
    annee = serializers.IntegerField()
    acquis = serializers.IntegerField()
    pris = serializers.IntegerField(read_only=True)
    restant = serializers.IntegerField(read_only=True)
    en_attente = serializers.IntegerField(read_only=True)
    disponible = serializers.IntegerField(read_only=True)

