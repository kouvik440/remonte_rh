from datetime import date

from rest_framework import serializers


class MasseSalarialeQuerySerializer(serializers.Serializer):
    periode_debut = serializers.RegexField(r"^\d{4}-(0[1-9]|1[0-2])$")
    periode_fin = serializers.RegexField(r"^\d{4}-(0[1-9]|1[0-2])$")
    departement = serializers.IntegerField(required=False, min_value=1)

    def validate_periode_debut(self, value):
        return self._validate_calendar_period(value, "periode_debut")

    def validate_periode_fin(self, value):
        return self._validate_calendar_period(value, "periode_fin")

    @staticmethod
    def _validate_calendar_period(value, field):
        year, month = map(int, value.split("-"))
        try:
            date(year, month, 1)
        except ValueError:
            raise serializers.ValidationError("L'année doit être comprise entre 1 et 9999.")
        return value

    def validate(self, attrs):
        start = attrs.get("periode_debut")
        end = attrs.get("periode_fin")
        if start and end and start > end:
            raise serializers.ValidationError(
                {"periode_fin": "La période de fin doit être égale ou postérieure à la période de début."}
            )
        return attrs


class MasseSalarialeEvolutionQuerySerializer(MasseSalarialeQuerySerializer):
    granularite = serializers.ChoiceField(
        choices=("mensuelle", "annuelle"),
        default="mensuelle",
        required=False,
    )


class MasseSalarialeExportQuerySerializer(MasseSalarialeEvolutionQuerySerializer):
    format_fichier = serializers.ChoiceField(choices=("csv", "xlsx", "pdf"))
