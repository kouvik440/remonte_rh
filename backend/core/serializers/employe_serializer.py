from rest_framework import serializers

from core.models import Employe, EmployeHistorique


class EmployeeRoleSerializer(serializers.Serializer):
    role_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
    )


class EmployeSerializer(serializers.ModelSerializer):
    poste_nom = serializers.SerializerMethodField()
    responsable_nom = serializers.SerializerMethodField()
    types_contrat_actuels = serializers.SerializerMethodField()
    postes_actuels = serializers.SerializerMethodField()

    def get_poste_nom(self, employee):
        return ", ".join(item["nom"] for item in self.get_postes_actuels(employee))

    def get_postes_actuels(self, employee):
        return list({contract.poste_id: {"id": contract.poste_id, "nom": contract.poste.nom}
            for contract in getattr(employee, "contrats_actuels", []) if contract.poste_id}.values())

    def get_responsable_nom(self, employee):
        return employee.responsable.get_full_name() if employee.responsable_id else ""

    def get_types_contrat_actuels(self, employee):
        return list({item.pk: {"id": item.pk, "libelle": item.type}
            for contract in getattr(employee, "contrats_actuels", []) for item in contract.type.all()}.values())
    roles = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Employe
        fields = [
            "id",
            "matricule",
            "email",
            "nom",
            "prenom",
            "date_naissance",
            "adresse",
            "telephone",
            "num_secu_sociale",
            "date_entree",
            "date_sortie",
            "statut",
            "is_active",
            "last_login",
            "department",
            "responsable", "responsable_nom", "poste_nom", "postes_actuels", "types_contrat_actuels",
            "roles",
        ]


class EmployeWriteSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    roles = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
    )

    class Meta:
        model = Employe
        fields = [
            "id",
            "matricule",
            "email",
            "password",
            "nom",
            "prenom",
            "date_naissance",
            "adresse",
            "telephone",
            "num_secu_sociale",
            "date_entree",
            "date_sortie",
            "statut",
            "is_active",
            "last_login",
            "department",
            "responsable",
            "roles",
        ]

    def validate(self, attrs):
        if "poste_nom" in self.initial_data:
            raise serializers.ValidationError({"poste_nom": "Sélectionnez le poste dans le contrat de l'employé."})
        if self.instance is None and not attrs.get("password"):
            raise serializers.ValidationError(
                {"password": "Le mot de passe est requis pour créer un compte."}
            )
        date_entree = attrs.get("date_entree")
        date_sortie = attrs.get("date_sortie")
        if date_entree and date_sortie and date_sortie < date_entree:
            raise serializers.ValidationError(
                {"date_sortie": "La date de sortie doit être après la date d'entrée."}
            )
        return attrs


class EmployeQuerySerializer(serializers.Serializer):
    poste = serializers.CharField(max_length=150, required=False)
    type_contrat = serializers.IntegerField(min_value=1, required=False)


class EmployeHistoriqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeHistorique
        fields = ["id", "categorie", "objet_id", "operation", "avant", "apres", "date_evenement", "auteur_nom"]
        read_only_fields = fields

