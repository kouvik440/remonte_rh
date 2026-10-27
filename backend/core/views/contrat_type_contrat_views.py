from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.services.contrat_type_contrat_service import contrat_type_contrat_service
from core.models import ContratTypeContrat
from core.permissions import HasResourceCrudPermission
from core.serializers.contrat_type_contrat_serializer import ContratTypeContratSerializer


class ContratTypeContratListView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "contrat_type_contrat"
    service = contrat_type_contrat_service

    def get(self, request):
        return Response(ContratTypeContratSerializer(self.service.get_all(), many=True).data)

    def post(self, request):
        serializer = ContratTypeContratSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        contrat_type_contrat = self.service.create(serializer.validated_data, actor=request.user)
        return Response(ContratTypeContratSerializer(contrat_type_contrat).data, status=status.HTTP_201_CREATED)


class ContratTypeContratDetailView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "contrat_type_contrat"
    service = contrat_type_contrat_service

    def get(self, request, contrat_type_contrat_id):
        try:
            return Response(ContratTypeContratSerializer(self.service.get(contrat_type_contrat_id)).data)
        except ContratTypeContrat.DoesNotExist:
            return Response({"detail": "Liaison contrat-type non trouvée"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, contrat_type_contrat_id):
        try:
            contrat_type_contrat = self.service.get(contrat_type_contrat_id)
        except ContratTypeContrat.DoesNotExist:
            return Response({"detail": "Liaison contrat-type non trouvée"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ContratTypeContratSerializer(contrat_type_contrat, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        contrat_type_contrat = self.service.update(contrat_type_contrat_id, serializer.validated_data, actor=request.user)
        return Response(ContratTypeContratSerializer(contrat_type_contrat).data)

    def delete(self, request, contrat_type_contrat_id):
        try:
            self.service.delete(contrat_type_contrat_id, actor=request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ContratTypeContrat.DoesNotExist:
            return Response({"detail": "Liaison contrat-type non trouvée"}, status=status.HTTP_404_NOT_FOUND)
