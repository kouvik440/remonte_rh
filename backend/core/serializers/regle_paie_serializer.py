from decimal import Decimal, InvalidOperation

from rest_framework import serializers

from core.models import ReglePaie


class ReglePaieSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReglePaie
        fields = [
            "id",
            "code",
            "nom",
            "pays",
            "devise",
            "date_debut",
            "date_fin",
            "actif",
            "heures_mensuelles",
            "jours_ouvres_semaine",
            "decimales_montant",
            "plafond_cnss",
            "taux_cnss_salarial",
            "taux_cnss_patronal",
            "taux_tpa_patronal",
            "abattement_professionnel",
            "plafond_deduction_retraite",
            "tranches_iuts",
            "reductions_iuts_charges",
            "source_reference",
            "valide",
            "date_creation",
        ]
        read_only_fields = ["valide", "date_creation"]

    def validate_tranches_iuts(self, value):
        if not isinstance(value, list) or not value:
            raise serializers.ValidationError("Définissez au moins une tranche IUTS.")

        tranches = []
        for item in value:
            if not isinstance(item, dict):
                raise serializers.ValidationError("Chaque tranche doit être un objet.")
            try:
                minimum = Decimal(str(item["minimum"]))
                maximum = (
                    Decimal(str(item["maximum"]))
                    if item.get("maximum") is not None
                    else None
                )
                taux = Decimal(str(item["taux"]))
            except (KeyError, TypeError, InvalidOperation):
                raise serializers.ValidationError(
                    "Chaque tranche exige minimum, maximum et taux numérique."
                )
            if minimum < 0 or not 0 <= taux <= 1:
                raise serializers.ValidationError("Minimum ou taux de tranche invalide.")
            if maximum is not None and maximum <= minimum:
                raise serializers.ValidationError("Le maximum doit dépasser le minimum.")
            tranches.append((minimum, maximum))

        tranches.sort(key=lambda item: item[0])
        if tranches[0][0] != 0:
            raise serializers.ValidationError("La première tranche doit commencer à zéro.")
        for index, (_, maximum) in enumerate(tranches[:-1]):
            if maximum != tranches[index + 1][0]:
                raise serializers.ValidationError(
                    "Les tranches doivent être contiguës, sans chevauchement."
                )
        if tranches[-1][1] is not None:
            raise serializers.ValidationError("La dernière tranche doit être sans plafond.")
        return value

    def validate_reductions_iuts_charges(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Les réductions doivent être une liste.")
        charges_vues = set()
        for item in value:
            if not isinstance(item, dict):
                raise serializers.ValidationError("Chaque réduction doit être un objet.")
            try:
                charges = int(item["charges"])
                taux = Decimal(str(item["taux"]))
            except (KeyError, TypeError, ValueError, InvalidOperation):
                raise serializers.ValidationError("Chaque réduction exige charges et taux.")
            if not 0 <= charges <= 4 or not 0 <= taux <= 1:
                raise serializers.ValidationError("Nombre de charges ou taux invalide.")
            if charges in charges_vues:
                raise serializers.ValidationError("Une charge ne peut être configurée qu'une fois.")
            charges_vues.add(charges)
        return value

    def validate(self, attrs):
        if "valide" in self.initial_data:
            raise serializers.ValidationError(
                {"valide": "Utilisez l'action dédiée pour valider ce profil."}
            )
        rate_fields = (
            "taux_cnss_salarial",
            "taux_cnss_patronal",
            "taux_tpa_patronal",
            "abattement_professionnel",
            "plafond_deduction_retraite",
        )
        for field in rate_fields:
            value = attrs.get(field, getattr(self.instance, field, None) if self.instance else None)
            if value is not None and not 0 <= value <= 1:
                raise serializers.ValidationError({field: "Le taux doit être compris entre 0 et 1."})

        date_debut = attrs.get(
            "date_debut",
            self.instance.date_debut if self.instance else None,
        )
        date_fin = attrs.get(
            "date_fin",
            self.instance.date_fin if self.instance else None,
        )
        if date_fin and date_debut and date_fin < date_debut:
            raise serializers.ValidationError(
                {"date_fin": "La fin doit suivre le début d'effet."}
            )
        heures_mensuelles = attrs.get(
            "heures_mensuelles",
            self.instance.heures_mensuelles if self.instance else None,
        )
        plafond_cnss = attrs.get(
            "plafond_cnss",
            self.instance.plafond_cnss if self.instance else None,
        )
        if heures_mensuelles is not None and heures_mensuelles <= 0:
            raise serializers.ValidationError(
                {"heures_mensuelles": "Le nombre d'heures doit être positif."}
            )
        if plafond_cnss is not None and plafond_cnss <= 0:
            raise serializers.ValidationError(
                {"plafond_cnss": "Le plafond CNSS doit être positif."}
            )
        jours_ouvres = attrs.get(
            "jours_ouvres_semaine",
            self.instance.jours_ouvres_semaine if self.instance else 5,
        )
        if jours_ouvres != 5:
            raise serializers.ValidationError(
                {"jours_ouvres_semaine": "Le moteur actuel suppose du lundi au vendredi."}
            )
        pays = attrs.get("pays", self.instance.pays if self.instance else "BF")
        devise = attrs.get("devise", self.instance.devise if self.instance else "XOF")
        if pays != "BF" or devise != "XOF":
            raise serializers.ValidationError(
                {"devise": "Ce profil de calcul concerne uniquement le Burkina Faso et le XOF."}
            )
        decimal_places = attrs.get(
            "decimales_montant",
            self.instance.decimales_montant if self.instance else 0,
        )
        if decimal_places > 2:
            raise serializers.ValidationError(
                {"decimales_montant": "Le FCFA est calculé au maximum au centime dans ce moteur."}
            )
        source_reference = attrs.get(
            "source_reference",
            self.instance.source_reference if self.instance else "",
        )
        if not source_reference.strip():
            raise serializers.ValidationError(
                {"source_reference": "Une référence des règles appliquées est requise."}
            )
        return attrs
