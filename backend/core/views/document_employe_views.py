from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.services.document_employe_service import document_employe_service
from core.models import DocumentEmploye
from core.permissions import HasDocumentEmployeeAccess
from core.services.authentication_service import authentication_service
from core.serializers.document_employe_serializer import DocumentEmployeSerializer


class DocumentEmployeListView(APIView):
    permission_classes = [HasDocumentEmployeeAccess]
    permission_resource = "document_employe"
    service = document_employe_service

    def get(self, request):
        links = self.service.get_all() if authentication_service.has_permission(request.user, "document.manage") else self.service.get_for_employee(request.user.pk)
        return Response(DocumentEmployeSerializer(links, many=True).data)

    def post(self, request):
        serializer = DocumentEmployeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        document_employe = self.service.create(serializer.validated_data)
        return Response(DocumentEmployeSerializer(document_employe).data, status=status.HTTP_201_CREATED)


class DocumentEmployeDetailView(APIView):
    permission_classes = [HasDocumentEmployeeAccess]
    permission_resource = "document_employe"
    service = document_employe_service

    def get(self, request, document_employe_id):
        try:
            link = self.service.get(document_employe_id)
            self.check_object_permissions(request, link)
            return Response(DocumentEmployeSerializer(link).data)
        except DocumentEmploye.DoesNotExist:
            return Response({"detail": "Liaison document-employé non trouvée"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, document_employe_id):
        try:
            document_employe = self.service.get(document_employe_id)
        except DocumentEmploye.DoesNotExist:
            return Response({"detail": "Liaison document-employé non trouvée"}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, document_employe)
        serializer = DocumentEmployeSerializer(document_employe, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        document_employe = self.service.update(document_employe_id, serializer.validated_data)
        return Response(DocumentEmployeSerializer(document_employe).data)

    def delete(self, request, document_employe_id):
        try:
            link = self.service.get(document_employe_id)
            self.check_object_permissions(request, link)
            self.service.delete(document_employe_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except DocumentEmploye.DoesNotExist:
            return Response({"detail": "Liaison document-employé non trouvée"}, status=status.HTTP_404_NOT_FOUND)
