from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.services.ordre_virement_service import ordre_virement_service
from core.models import OrdreVirement
from core.permissions import HasOrdreVirementDecisionPermission, HasResourceCrudPermission
from core.serializers.ordre_virement_serializer import OrdreVirementMotifSerializer, OrdreVirementSerializer


class OrdreVirementListView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "ordre_virement"
    service = ordre_virement_service

    def get(self, request):
        return Response(OrdreVirementSerializer(self.service.get_all(), many=True).data)

    def post(self, request):
        serializer = OrdreVirementSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        ordre_virement = self.service.create(serializer.validated_data)
        return Response(OrdreVirementSerializer(ordre_virement).data, status=status.HTTP_201_CREATED)


class OrdreVirementActionView(APIView):
    permission_classes = [HasOrdreVirementDecisionPermission]
    permission_resource = "ordre_virement"
    service = ordre_virement_service

    def post(self, request, ordre_virement_id, action):
        serializer = OrdreVirementMotifSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            ordre = getattr(self.service, action)(ordre_virement_id, decideur_id=request.user.pk, **serializer.validated_data)
        except OrdreVirement.DoesNotExist:
            return Response({"detail": "Ordre de virement non trouvé"}, status=status.HTTP_404_NOT_FOUND)
        return Response(OrdreVirementSerializer(ordre).data)


class OrdreVirementDetailView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "ordre_virement"
    service = ordre_virement_service

    def get(self, request, ordre_virement_id):
        try:
            return Response(OrdreVirementSerializer(self.service.get(ordre_virement_id)).data)
        except OrdreVirement.DoesNotExist:
            return Response({"detail": "Ordre de virement non trouvé"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, ordre_virement_id):
        try:
            ordre_virement = self.service.get(ordre_virement_id)
        except OrdreVirement.DoesNotExist:
            return Response({"detail": "Ordre de virement non trouvé"}, status=status.HTTP_404_NOT_FOUND)
        serializer = OrdreVirementSerializer(ordre_virement, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        ordre_virement = self.service.update(ordre_virement_id, serializer.validated_data)
        return Response(OrdreVirementSerializer(ordre_virement).data)

    def delete(self, request, ordre_virement_id):
        try:
            self.service.delete(ordre_virement_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except OrdreVirement.DoesNotExist:
            return Response({"detail": "Ordre de virement non trouvé"}, status=status.HTTP_404_NOT_FOUND)
