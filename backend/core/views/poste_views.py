from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.services.poste_service import poste_service
from core.models import Poste
from core.permissions import HasResourceCrudPermission
from core.serializers.poste_serializer import PosteSerializer


class PosteListView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "poste"
    service = poste_service

    def get(self, request):
        return Response(PosteSerializer(self.service.get_all(), many=True).data)

    def post(self, request):
        serializer = PosteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        poste = self.service.create(serializer.validated_data, actor=request.user)
        return Response(PosteSerializer(poste).data, status=status.HTTP_201_CREATED)


class PosteDetailView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "poste"
    service = poste_service

    def get(self, request, poste_id):
        try:
            return Response(PosteSerializer(self.service.get(poste_id)).data)
        except Poste.DoesNotExist:
            return Response({"detail": "Poste non trouvé"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, poste_id):
        try:
            poste = self.service.get(poste_id)
        except Poste.DoesNotExist:
            return Response({"detail": "Poste non trouvé"}, status=status.HTTP_404_NOT_FOUND)
        serializer = PosteSerializer(poste, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        poste = self.service.update(poste_id, serializer.validated_data, actor=request.user)
        return Response(PosteSerializer(poste).data)

    def delete(self, request, poste_id):
        try:
            self.service.delete(poste_id, actor=request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Poste.DoesNotExist:
            return Response({"detail": "Poste non trouvé"}, status=status.HTTP_404_NOT_FOUND)
