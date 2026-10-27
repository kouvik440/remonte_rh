from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.response import Response
from rest_framework.views import APIView

from core.services.solde_conge_service import solde_conge_service
from core.permissions import HasResourceCrudPermission
from core.serializers.solde_conge_serializer import (
    SoldeCongeSerializer,
)
from core.services.authentication_service import authentication_service


class SoldeCongeListView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "solde_conge"
    service = solde_conge_service

    def get(self, request):
        year_value = request.query_params.get("annee", timezone.localdate().year)
        try:
            year = int(year_value)
            if year < 1 or year > 9999:
                raise ValueError
        except (TypeError, ValueError):
            return Response(
                {"annee": ["L'année doit être un entier entre 1 et 9999."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        can_read_all = authentication_service.has_permission(
            request.user,
            "demande_absence.update",
        )
        employee_id = None if can_read_all else request.user.pk
        if can_read_all and request.query_params.get("employe"):
            try:
                employee_id = int(request.query_params["employe"])
            except ValueError:
                return Response(
                    {"employe": ["L'identifiant doit être un entier."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        balances = self.service.get_balances(year, employee_id)
        return Response(SoldeCongeSerializer(balances, many=True).data)

    def post(self, request):
        raise MethodNotAllowed("POST", detail="Le droit annuel est défini dans le type de congé, sans quota individuel.")


class SoldeCongeDetailView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "solde_conge"

    def put(self, request, balance_id):
        raise MethodNotAllowed("PUT", detail="Modifiez le droit annuel du type de congé pour tous les employés.")
