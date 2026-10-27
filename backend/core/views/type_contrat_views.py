from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.services.type_contrat_service import type_contrat_service
from core.models import TypeContrat
from core.permissions import HasResourceCrudPermission
from core.serializers.type_contrat_serializer import TypeContratSerializer


class TypeContratListView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "type_contrat"
    service = type_contrat_service

    def get(self, request):
        return Response(TypeContratSerializer(self.service.get_all(), many=True).data)

    def post(self, request):
        serializer = TypeContratSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        type_contrat = self.service.create(serializer.validated_data)
        return Response(TypeContratSerializer(type_contrat).data, status=status.HTTP_201_CREATED)


class TypeContratDetailView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "type_contrat"
    service = type_contrat_service

    def get(self, request, type_contrat_id):
        try:
            return Response(TypeContratSerializer(self.service.get(type_contrat_id)).data)
        except TypeContrat.DoesNotExist:
            return Response({"detail": "Type de contrat non trouvé"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, type_contrat_id):
        try:
            type_contrat = self.service.get(type_contrat_id)
        except TypeContrat.DoesNotExist:
            return Response({"detail": "Type de contrat non trouvé"}, status=status.HTTP_404_NOT_FOUND)
        serializer = TypeContratSerializer(type_contrat, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        type_contrat = self.service.update(type_contrat_id, serializer.validated_data)
        return Response(TypeContratSerializer(type_contrat).data)

    def delete(self, request, type_contrat_id):
        try:
            self.service.delete(type_contrat_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except TypeContrat.DoesNotExist:
            return Response({"detail": "Type de contrat non trouvé"}, status=status.HTTP_404_NOT_FOUND)
