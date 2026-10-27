from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import ReglePaie
from core.permissions import HasPaieCalculationPermission, HasResourceCrudPermission
from core.serializers.regle_paie_serializer import ReglePaieSerializer
from core.services.regle_paie_service import regle_paie_service


class ReglePaieListView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "paie"
    service = regle_paie_service

    def get(self, request):
        return Response(ReglePaieSerializer(self.service.get_all(), many=True).data)

    def post(self, request):
        serializer = ReglePaieSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        regle = self.service.create(serializer.validated_data)
        return Response(
            ReglePaieSerializer(regle).data,
            status=status.HTTP_201_CREATED,
        )


class ReglePaieDetailView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "paie"
    service = regle_paie_service

    def get(self, request, regle_id):
        try:
            regle = self.service.get(regle_id)
        except ReglePaie.DoesNotExist:
            return Response({"detail": "Règle de paie non trouvée"}, status=404)
        return Response(ReglePaieSerializer(regle).data)

    def put(self, request, regle_id):
        try:
            regle = self.service.get(regle_id)
        except ReglePaie.DoesNotExist:
            return Response({"detail": "Règle de paie non trouvée"}, status=404)
        serializer = ReglePaieSerializer(regle, data=request.data)
        serializer.is_valid(raise_exception=True)
        regle = self.service.update(regle_id, serializer.validated_data)
        return Response(ReglePaieSerializer(regle).data)

    def delete(self, request, regle_id):
        try:
            self.service.delete(regle_id)
        except ReglePaie.DoesNotExist:
            return Response({"detail": "Règle de paie non trouvée"}, status=404)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReglePaieValiderView(APIView):
    permission_classes = [HasPaieCalculationPermission]
    service = regle_paie_service

    def post(self, request, regle_id):
        try:
            regle = self.service.validate(regle_id)
        except ReglePaie.DoesNotExist:
            return Response({"detail": "Règle de paie non trouvée"}, status=404)
        return Response(ReglePaieSerializer(regle).data)