from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import HasResourceCrudPermission
from core.serializers.contrat_serializer import ContratSerializer
from core.serializers.paie_serializer import PayrollContractQuerySerializer
from core.services.contrat_service import contrat_service


class PayrollContractContextView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "paie"
    service = contrat_service

    def get(self, request):
        query = PayrollContractQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        context = self.service.payroll_context(query.validated_data["employe"], query.validated_data["periode"])
        return Response({**context, "contracts": ContratSerializer(context["contracts"], many=True).data})
