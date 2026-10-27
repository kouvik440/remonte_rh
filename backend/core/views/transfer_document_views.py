from django.http import FileResponse
from django.utils.http import content_disposition_header
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import OrdreVirement
from core.permissions import HasTransferDocumentPermission
from core.serializers.transfer_document_serializer import TransferDocumentRequestSerializer
from core.services.ordre_virement_service import ordre_virement_service
from core.services.transfer_document_service import transfer_document_service


class TransferDocumentContextView(APIView):
    permission_classes = [HasTransferDocumentPermission]
    service = transfer_document_service

    def get(self, request, order_id):
        try:
            return Response(self.service.context(order_id))
        except OrdreVirement.DoesNotExist:
            return Response({"detail": "Ordre de virement introuvable."}, status=404)


class TransferDocumentView(APIView):
    permission_classes = [HasTransferDocumentPermission]
    service = transfer_document_service
    orders = ordre_virement_service

    def post(self, request, order_id):
        serializer = TransferDocumentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            order = self.service.generate(order_id, serializer.validated_data, request.user.pk)
        except OrdreVirement.DoesNotExist:
            return Response({"detail": "Ordre de virement introuvable."}, status=404)
        return Response({"ordre": order.pk, "document_disponible": True, "date_generation": order.document_genere_le})

    def get(self, request, order_id):
        try:
            order = self.orders.get(order_id)
        except OrdreVirement.DoesNotExist:
            return Response({"detail": "Ordre de virement introuvable."}, status=404)
        if not order.document_pdf:
            return Response({"detail": "Le document n’a pas encore été généré."}, status=404)
        try:
            document = order.document_pdf.open("rb")
        except FileNotFoundError:
            return Response({"detail": "Le document archivé est introuvable. Contactez le gestionnaire."}, status=404)
        response = FileResponse(document, content_type="application/pdf")
        response["Content-Disposition"] = content_disposition_header(True, f"ordre-virement-BF-{order.pk}.pdf")
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response
