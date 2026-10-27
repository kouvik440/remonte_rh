from rest_framework import serializers

from core.models import TypeContrat


class TypeContratSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeContrat
        fields = ["id", "type", "description"]
