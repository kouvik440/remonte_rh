from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.services.document_service import document_service
from core.models import Document
from core.permissions import HasDocumentAccess
from core.services.authentication_service import authentication_service
from core.serializers.document_serializer import DocumentSerializer


class DocumentListView(APIView):
    permission_classes = [HasDocumentAccess]
    permission_resource = "document"
    service = document_service

    def get(self, request):
        documents = self.service.get_all() if authentication_service.has_permission(request.user, "document.manage") else self.service.get_for_employee(request.user.pk)
        return Response(DocumentSerializer(documents, many=True).data)

    def post(self, request):
        serializer = DocumentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        document = self.service.create(serializer.validated_data)
        return Response(DocumentSerializer(document).data, status=status.HTTP_201_CREATED)


class DocumentDetailView(APIView):
    permission_classes = [HasDocumentAccess]
    permission_resource = "document"
    service = document_service

    def get(self, request, document_id):
        try:
            document = self.service.get(document_id)
            self.check_object_permissions(request, document)
            return Response(DocumentSerializer(document).data)
        except Document.DoesNotExist:
            return Response({"detail": "Document non trouvé"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, document_id):
        try:
            document = self.service.get(document_id)
        except Document.DoesNotExist:
            return Response({"detail": "Document non trouvé"}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, document)
        serializer = DocumentSerializer(document, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        document = self.service.update(document_id, serializer.validated_data)
        return Response(DocumentSerializer(document).data)

    def delete(self, request, document_id):
        try:
            document = self.service.get(document_id)
            self.check_object_permissions(request, document)
            self.service.delete(document_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Document.DoesNotExist:
            return Response({"detail": "Document non trouvé"}, status=status.HTTP_404_NOT_FOUND)
