from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.services.contrat_service import contrat_service
from core.models import Contrat
from core.permissions import HasResourceCrudPermission
from core.serializers.contrat_serializer import ContratQuerySerializer, ContratSerializer


class ContratListView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "contrat"
    service = contrat_service

    def get(self, request):
        query = ContratQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        return Response(ContratSerializer(self.service.get_all(query.validated_data.get("employe")), many=True).data)

    def post(self, request):
        serializer = ContratSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        contrat = self.service.create(serializer.validated_data, actor=request.user)
        return Response(ContratSerializer(contrat).data, status=status.HTTP_201_CREATED)


class ContratDetailView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "contrat"
    service = contrat_service

    def get(self, request, contrat_id):
        try:
            return Response(ContratSerializer(self.service.get(contrat_id)).data)
        except Contrat.DoesNotExist:
            return Response({"detail": "Contrat non trouvé"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, contrat_id):
        try:
            contrat = self.service.get(contrat_id)
        except Contrat.DoesNotExist:
            return Response({"detail": "Contrat non trouvé"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ContratSerializer(contrat, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        contrat = self.service.update(contrat_id, serializer.validated_data, actor=request.user)
        return Response(ContratSerializer(contrat).data)

    def delete(self, request, contrat_id):
        try:
            self.service.delete(contrat_id, actor=request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Contrat.DoesNotExist:
            return Response({"detail": "Contrat non trouvé"}, status=status.HTTP_404_NOT_FOUND)
