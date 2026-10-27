from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.services.type_document_service import type_document_service
from core.models import TypeDocument
from core.permissions import HasResourceCrudPermission
from core.serializers.type_document_serializer import TypeDocumentSerializer


class TypeDocumentListView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "type_document"
    service = type_document_service

    def get(self, request):
        return Response(TypeDocumentSerializer(self.service.get_all(), many=True).data)

    def post(self, request):
        serializer = TypeDocumentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        type_document = self.service.create(serializer.validated_data)
        return Response(TypeDocumentSerializer(type_document).data, status=status.HTTP_201_CREATED)


class TypeDocumentDetailView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "type_document"
    service = type_document_service

    def get(self, request, type_document_id):
        try:
            return Response(TypeDocumentSerializer(self.service.get(type_document_id)).data)
        except TypeDocument.DoesNotExist:
            return Response({"detail": "Type de document non trouvé"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, type_document_id):
        try:
            type_document = self.service.get(type_document_id)
        except TypeDocument.DoesNotExist:
            return Response({"detail": "Type de document non trouvé"}, status=status.HTTP_404_NOT_FOUND)
        serializer = TypeDocumentSerializer(type_document, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        type_document = self.service.update(type_document_id, serializer.validated_data)
        return Response(TypeDocumentSerializer(type_document).data)

    def delete(self, request, type_document_id):
        try:
            self.service.delete(type_document_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except TypeDocument.DoesNotExist:
            return Response({"detail": "Type de document non trouvé"}, status=status.HTTP_404_NOT_FOUND)
