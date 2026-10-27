from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import HasResourceCrudPermission
from core.serializers.tgm_serializer import TgmQuerySerializer
from core.services.tgm_service import tgm_service


class TgmListView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "paie"
    service = tgm_service

    def get(self, request):
        serializer = TgmQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data
        return Response(
            self.service.calculate(
                params["periode_debut"],
                params["periode_fin"],
            )
        )
