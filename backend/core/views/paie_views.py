from django.http import FileResponse
from django.utils.http import content_disposition_header
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Paie, ReglePaie
from core.permissions import (
    HasPaieBulletinGenerationPermission,
    HasPaieCalculationPermission,
    HasResourceCrudPermission,
)
from core.services.authentication_service import authentication_service
from core.serializers.element_variable_paie_serializer import (
    PaieAnnulationRequestSerializer,
    PaieCalculationRequestSerializer,
    PaiePaiementRequestSerializer,
)
from core.serializers.paie_serializer import PaieSerializer, PersonalPayslipSerializer
from core.services.paie_calculation_service import paie_calculation_service
from core.services.paie_service import paie_service


class PersonalPayslipListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payrolls = paie_service.for_employee(request.user.pk)
        response = Response(PersonalPayslipSerializer(payrolls, many=True).data)
        response["Cache-Control"] = "private, no-store"
        return response


class PaieListView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "paie"
    service = paie_service

    def get(self, request):
        return Response(PaieSerializer(self.service.get_all(), many=True).data)

    def post(self, request):
        serializer = PaieSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        paie = self.service.create(serializer.validated_data)
        return Response(PaieSerializer(paie).data, status=status.HTTP_201_CREATED)


class PaieDetailView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "paie"
    service = paie_service

    def get(self, request, paie_id):
        try:
            return Response(PaieSerializer(self.service.get(paie_id)).data)
        except Paie.DoesNotExist:
            return Response({"detail": "Paie non trouvée"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, paie_id):
        try:
            paie = self.service.get(paie_id)
        except Paie.DoesNotExist:
            return Response({"detail": "Paie non trouvée"}, status=status.HTTP_404_NOT_FOUND)
        serializer = PaieSerializer(paie, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        paie = self.service.update(paie_id, serializer.validated_data)
        return Response(PaieSerializer(paie).data)

    def delete(self, request, paie_id):
        try:
            self.service.delete(paie_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Paie.DoesNotExist:
            return Response({"detail": "Paie non trouvée"}, status=status.HTTP_404_NOT_FOUND)


class PaieCalculerView(APIView):
    permission_classes = [HasPaieCalculationPermission]
    service = paie_calculation_service

    def post(self, request, paie_id):
        serializer = PaieCalculationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            paie = self.service.calculate(
                paie_id,
                regle_id=serializer.validated_data.get("regle_paie"),
                charges_familiales=serializer.validated_data.get(
                    "charges_familiales",
                    0,
                ),
            )
        except Paie.DoesNotExist:
            return Response(
                {"detail": "Paie non trouvée"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ReglePaie.DoesNotExist:
            return Response(
                {"regle_paie": "Profil de règles non trouvé"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(PaieSerializer(paie).data)


class PaieValiderView(APIView):
    permission_classes = [HasPaieCalculationPermission]
    service = paie_service

    def post(self, request, paie_id):
        try:
            paie = self.service.valider(paie_id, request.user.pk)
        except Paie.DoesNotExist:
            return Response({"detail": "Paie non trouvée"}, status=status.HTTP_404_NOT_FOUND)
        return Response(PaieSerializer(paie).data)


class PaieAnnulerView(APIView):
    permission_classes = [HasPaieCalculationPermission]
    service = paie_service

    def post(self, request, paie_id):
        serializer = PaieAnnulationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            paie = self.service.annuler(
                paie_id,
                request.user.pk,
                serializer.validated_data["motif"],
            )
        except Paie.DoesNotExist:
            return Response({"detail": "Paie non trouvée"}, status=status.HTTP_404_NOT_FOUND)
        return Response(PaieSerializer(paie).data)


class PaieMarquerPayeeView(APIView):
    permission_classes = [HasPaieCalculationPermission]
    service = paie_service

    def post(self, request, paie_id):
        serializer = PaiePaiementRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            paie = self.service.marquer_payee(
                paie_id,
                serializer.validated_data["ordre_virement"],
            )
        except Paie.DoesNotExist:
            return Response({"detail": "Paie non trouvée"}, status=status.HTTP_404_NOT_FOUND)
        return Response(PaieSerializer(paie).data)


class PaieBulletinView(APIView):
    service = paie_service

    def post(self, request, paie_id):
        try:
            paie = self.service.generate_bulletin(paie_id)
        except Paie.DoesNotExist:
            return Response({"detail": "Paie non trouvée"}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {
                "paie": paie.pk,
                "bulletin_disponible": True,
                "url": f"/api/paiements/{paie.pk}/bulletin/",
            },
            status=status.HTTP_200_OK,
        )

    def get_permissions(self):
        if self.request.method == "POST":
            return [HasPaieBulletinGenerationPermission()]
        return [IsAuthenticated()]

    def get(self, request, paie_id):
        try:
            paie = self.service.get(paie_id)
        except Paie.DoesNotExist:
            return Response({"detail": "Paie non trouvée"}, status=status.HTTP_404_NOT_FOUND)
        is_owner = paie.employe_id == request.user.pk
        can_read_payroll = authentication_service.has_permission(request.user, "paie.read")
        if not is_owner and not can_read_payroll:
            raise PermissionDenied("Vous ne pouvez pas télécharger ce bulletin.")
        if not paie.bulletin_pdf:
            return Response({"detail": "Le bulletin n'a pas encore été généré."}, status=status.HTTP_404_NOT_FOUND)

        try:
            bulletin = paie.bulletin_pdf.open("rb")
        except FileNotFoundError:
            return Response({"detail": "Le fichier du bulletin est introuvable. Contactez le gestionnaire de paie."}, status=status.HTTP_404_NOT_FOUND)
        response = FileResponse(bulletin, content_type="application/pdf")
        filename = f"bulletin-paie-{paie.periode}-{paie.pk}.pdf"
        response["Content-Disposition"] = content_disposition_header(True, filename)
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response
