from rest_framework import serializers

from core.models import DocumentEmploye


class DocumentEmployeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentEmploye
        fields = ["id", "document", "employe", "date_depot"]
