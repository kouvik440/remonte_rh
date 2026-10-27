from rest_framework import serializers

from core.models import Departement


class DepartementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departement
        fields = ["id", "nom", "code"]
        read_only_fields = ["id", "code"]
