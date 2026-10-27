from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.services.coordonnees_bancaires_service import coordonnees_bancaires_service
from core.models import CoordonneesBancaires
from core.permissions import HasCoordonneesBancairesAccess
from core.serializers.coordonnees_bancaires_serializer import CoordonneesBancairesSerializer
from core.services.authentication_service import authentication_service


class CoordonneesBancairesListView(APIView):
    permission_classes = [HasCoordonneesBancairesAccess]
    permission_resource = "coordonnees_bancaires"
    service = coordonnees_bancaires_service

    def get(self, request):
        if authentication_service.has_permission(
            request.user,
            "coordonnees_bancaires.manage",
        ):
            coordonnees = self.service.get_all()
        else:
            coordonnees = self.service.get_for_employee(request.user.pk)
        return Response(CoordonneesBancairesSerializer(coordonnees, many=True).data)

    def post(self, request):
        serializer = CoordonneesBancairesSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = dict(serializer.validated_data)
        if authentication_service.has_permission(
            request.user,
            "coordonnees_bancaires.manage",
        ):
            if "employe" not in data:
                return Response(
                    {"employe": ["Ce champ est requis pour créer des coordonnées pour un tiers."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            data["employe"] = request.user
        coordonnees = self.service.create(data)
        return Response(CoordonneesBancairesSerializer(coordonnees).data, status=status.HTTP_201_CREATED)


class CoordonneesBancairesDetailView(APIView):
    permission_classes = [HasCoordonneesBancairesAccess]
    permission_resource = "coordonnees_bancaires"
    service = coordonnees_bancaires_service

    def get(self, request, coordonnees_bancaires_id):
        try:
            coordonnees = self.service.get(coordonnees_bancaires_id)
        except CoordonneesBancaires.DoesNotExist:
            return Response({"detail": "Coordonnées bancaires non trouvées"}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, coordonnees)
        return Response(CoordonneesBancairesSerializer(coordonnees).data)

    def put(self, request, coordonnees_bancaires_id):
        try:
            coordonnees = self.service.get(coordonnees_bancaires_id)
        except CoordonneesBancaires.DoesNotExist:
            return Response({"detail": "Coordonnées bancaires non trouvées"}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, coordonnees)
        serializer = CoordonneesBancairesSerializer(coordonnees, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = dict(serializer.validated_data)
        data.pop("employe", None)
        coordonnees = self.service.update(coordonnees_bancaires_id, data)
        return Response(CoordonneesBancairesSerializer(coordonnees).data)

    def delete(self, request, coordonnees_bancaires_id):
        try:
            coordonnees = self.service.get(coordonnees_bancaires_id)
        except CoordonneesBancaires.DoesNotExist:
            return Response({"detail": "Coordonnées bancaires non trouvées"}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, coordonnees)
        self.service.delete(coordonnees_bancaires_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
