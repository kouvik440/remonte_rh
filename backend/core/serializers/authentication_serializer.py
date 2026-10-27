from collections.abc import Mapping

from rest_framework import serializers


class StrictInputSerializer(serializers.Serializer):
    def _raise_for_unexpected_fields(self, data):
        if not isinstance(data, Mapping):
            return

        unexpected_fields = set(data) - set(self.fields)
        if unexpected_fields:
            raise serializers.ValidationError(
                {
                    field: ["Champ non autorisé."]
                    for field in sorted(unexpected_fields)
                } 
            )

    def to_internal_value(self, data):
        self._raise_for_unexpected_fields(data)
        return super().to_internal_value(data)


class LoginSerializer(StrictInputSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class LoginUserResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="employee.pk")
    email = serializers.EmailField(source="employee.email")
    nom = serializers.CharField(source="employee.nom")
    prenom = serializers.CharField(source="employee.prenom")
    is_staff = serializers.BooleanField(source="employee.is_staff")
    roles = serializers.ListField(child=serializers.CharField())
    permissions = serializers.ListField(child=serializers.CharField())


class LoginResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = serializers.SerializerMethodField()

    def get_user(self, instance):
        return LoginUserResponseSerializer(instance).data


class RefreshRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class CurrentUserUpdateSerializer(StrictInputSerializer):
    nom = serializers.CharField(max_length=100)
    prenom = serializers.CharField(max_length=100)


class ChangePasswordSerializer(StrictInputSerializer):
    ancien_mot_de_passe = serializers.CharField(write_only=True, trim_whitespace=False)
    nouveau_mot_de_passe = serializers.CharField(write_only=True, trim_whitespace=False)
    confirmation = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError
        from django.utils.translation import override
        user = self.context["request"].user
        if not user.check_password(attrs["ancien_mot_de_passe"]):
            raise serializers.ValidationError({"ancien_mot_de_passe": "Le mot de passe actuel est incorrect."})
        if attrs["nouveau_mot_de_passe"] != attrs["confirmation"]:
            raise serializers.ValidationError({"confirmation": "Les mots de passe ne correspondent pas."})
        if attrs["nouveau_mot_de_passe"] == attrs["ancien_mot_de_passe"]:
            raise serializers.ValidationError({"nouveau_mot_de_passe": "Choisissez un mot de passe différent de l'actuel."})
        try:
            with override("fr"):
                validate_password(attrs["nouveau_mot_de_passe"], user=user)
        except ValidationError as error:
            raise serializers.ValidationError({"nouveau_mot_de_passe": error.messages}) from error
        return attrs


class RefreshResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
