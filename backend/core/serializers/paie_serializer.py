from rest_framework import serializers

from core.models import Paie
from core.services.payroll_period import payroll_period_bounds


def validate_payroll_period(value):
    try:
        payroll_period_bounds(value)
    except serializers.ValidationError as error:
        raise serializers.ValidationError(error.detail["periode"]) from error
    return value


class PaieSerializer(serializers.ModelSerializer):
    employe_nom = serializers.CharField(source="employe.nom", read_only=True)
    employe_prenom = serializers.CharField(source="employe.prenom", read_only=True)
    employe_matricule = serializers.CharField(source="employe.matricule", read_only=True)
    bulletin_disponible = serializers.SerializerMethodField()
    bulletin_generable = serializers.SerializerMethodField()
    computed_fields = [
        "salaire_base",
        "salaire_brut",
        "salaire_net",
        "cout_charge",
        "cotisations",
        "devise",
        "detail_calcul",
        "statut",
        "date_calcul",
        "date_validation",
        "valideur",
        "date_paiement",
        "date_annulation",
        "annule_par",
        "motif_annulation",
    ]

    class Meta:
        model = Paie
        fields = [
            "id",
            "periode",
            "libelle",
            "salaire_base",
            "salaire_brut",
            "salaire_net",
            "cout_charge",
            "cotisations",
            "devise",
            "detail_calcul",
            "statut",
            "date_calcul",
            "date_validation",
            "valideur",
            "date_paiement",
            "date_annulation",
            "annule_par",
            "motif_annulation",
            "employe",
            "employe_nom",
            "employe_prenom",
            "employe_matricule",
            "ordre_virement",
            "bulletin_disponible",
            "bulletin_generable",
        ]
        validators = []
        read_only_fields = [
            "salaire_base",
            "salaire_brut",
            "salaire_net",
            "cout_charge",
            "cotisations",
            "devise",
            "detail_calcul",
            "statut",
            "date_calcul",
            "date_validation",
            "valideur",
            "date_paiement",
            "date_annulation",
            "annule_par",
            "motif_annulation",
        ]

    def get_bulletin_disponible(self, obj):
        return bool(obj.bulletin_pdf)

    def get_bulletin_generable(self, obj):
        return bool(
            obj.statut in ("VALIDEE", "PAYE")
            and obj.date_calcul
            and (obj.detail_calcul or {}).get("totaux")
        )

    def validate_periode(self, value):
        return validate_payroll_period(value)

    def validate(self, attrs):
        supplied_computed_fields = [
            field for field in self.computed_fields if field in self.initial_data
        ]
        if supplied_computed_fields:
            raise serializers.ValidationError(
                {
                    field: "Ce champ est produit par le calcul de paie et ne peut pas être saisi."
                    for field in supplied_computed_fields
                }
            )
        return attrs


class PayrollContractQuerySerializer(serializers.Serializer):
    employe = serializers.IntegerField(min_value=1)
    periode = serializers.CharField()

    def validate_periode(self, value):
        return validate_payroll_period(value)


class PersonalPayslipSerializer(serializers.ModelSerializer):
    bulletin_disponible = serializers.SerializerMethodField()

    def get_bulletin_disponible(self, obj):
        return bool(obj.bulletin_pdf)

    class Meta:
        model = Paie
        fields = ["id", "periode", "libelle", "salaire_brut", "salaire_net", "devise", "statut", "date_validation", "bulletin_disponible"]
        read_only_fields = fields
