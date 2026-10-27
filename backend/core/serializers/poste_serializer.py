from rest_framework import serializers

from core.models import Poste


class PosteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Poste
        fields = ["id", "nom", "description"]

    def validate_nom(self, value):
        matches = Poste.objects.filter(nom__iexact=value.strip())
        if self.instance:
            matches = matches.exclude(pk=self.instance.pk)
        if matches.exists():
            raise serializers.ValidationError("Un poste portant ce nom existe déjà.")
        return value.strip()
