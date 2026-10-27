from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.services.departement_service import departement_service
from core.models import Departement
from core.permissions import HasResourceCrudPermission
from core.serializers.departement_serializer import DepartementSerializer


class DepartementListView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "departement"
    service = departement_service

    def get(self, request):
        return Response(DepartementSerializer(self.service.get_all(), many=True).data)

    def post(self, request):
        serializer = DepartementSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        department = self.service.create(serializer.validated_data)
        return Response(DepartementSerializer(department).data, status=status.HTTP_201_CREATED)


class DepartementDetailView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "departement"
    service = departement_service

    def get(self, request, department_id):
        try:
            return Response(DepartementSerializer(self.service.get(department_id)).data)
        except Departement.DoesNotExist:
            return Response({"detail": "Département non trouvé"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, department_id):
        try:
            department = self.service.get(department_id)
        except Departement.DoesNotExist:
            return Response({"detail": "Département non trouvé"}, status=status.HTTP_404_NOT_FOUND)
        serializer = DepartementSerializer(department, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        department = self.service.update(department_id, serializer.validated_data)
        return Response(DepartementSerializer(department).data)

    def delete(self, request, department_id):
        try:
            self.service.delete(department_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Departement.DoesNotExist:
            return Response({"detail": "Département non trouvé"}, status=status.HTTP_404_NOT_FOUND)
