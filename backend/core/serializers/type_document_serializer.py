from rest_framework import serializers

from core.models import TypeDocument


class TypeDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeDocument
        read_only_fields = ["id", "code"]
        fields = ["id", "code", "libelle", "description", "is_active"]
