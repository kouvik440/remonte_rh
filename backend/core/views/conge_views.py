from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.services.conge_service import conge_service
from core.models import TypeConge
from core.permissions import HasResourceCrudPermission
from core.serializers.conge_serializer import TypeCongeSerializer


class TypeCongeListView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "conge"
    service = conge_service

    def get(self, request):
        return Response(
            TypeCongeSerializer(self.service.get_all_types(), many=True).data
        )

    def post(self, request):
        serializer = TypeCongeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        type_conge = self.service.create_type(serializer.validated_data)
        return Response(TypeCongeSerializer(type_conge).data, status=status.HTTP_201_CREATED)


class TypeCongeDetailView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "conge"
    service = conge_service

    def get(self, request, type_conge_id):
        try:
            return Response(TypeCongeSerializer(self.service.get_type(type_conge_id)).data)
        except TypeConge.DoesNotExist:
            return Response(
                {"detail": "Type de conge non trouve"}, status=status.HTTP_404_NOT_FOUND
            )

    def put(self, request, type_conge_id):
        try:
            existing_type = self.service.get_type(type_conge_id)
        except TypeConge.DoesNotExist:
            return Response(
                {"detail": "Type de conge non trouve"}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = TypeCongeSerializer(existing_type, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        type_conge = self.service.update_type(type_conge_id, serializer.validated_data)
        return Response(TypeCongeSerializer(type_conge).data)

    def delete(self, request, type_conge_id):
        try:
            self.service.delete_type(type_conge_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except TypeConge.DoesNotExist:
            return Response(
                {"detail": "Type de conge non trouve"}, status=status.HTTP_404_NOT_FOUND
            )
