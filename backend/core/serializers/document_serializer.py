from rest_framework import serializers

from core.models import Document, Employe


class DocumentSerializer(serializers.ModelSerializer):
    type_document_libelle = serializers.CharField(source="type_document.libelle", read_only=True)
    employes = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Employe.objects,
        required=False,
    )

    class Meta:
        model = Document
        fields = [
            "id",
            "type_document",
            "type_document_libelle",
            "fichier",
            "date_depot",
            "date_expiration",
            "employes",
        ]

    def validate(self, attrs):
        document_type = attrs.get("type_document")
        if document_type and not document_type.is_active and (
            self.instance is None or document_type.pk != self.instance.type_document_id
        ):
            raise serializers.ValidationError({"type_document": "Choisissez un type de document actif."})
        start = attrs.get("date_depot", self.instance.date_depot if self.instance else None)
        end = attrs.get("date_expiration", self.instance.date_expiration if self.instance else None)
        if start and end and end < start:
            raise serializers.ValidationError({"date_expiration": "L'expiration doit suivre la date de dépôt."})
        return attrs
