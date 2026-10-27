from rest_framework import serializers

from core.models import ContratTypeContrat


class ContratTypeContratSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContratTypeContrat
        fields = ["id", "contrat", "type_contrat"]
