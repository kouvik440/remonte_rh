from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import HasResourceCrudPermission
from core.serializers.cout_projet_serializer import CoutProjetQuerySerializer, RentabiliteProjetQuerySerializer
from core.services.cout_projet_service import cout_projet_service


class CoutProjetView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "paie"
    service = cout_projet_service

    def get(self, request):
        serializer = CoutProjetQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data
        return Response(
            self.service.summarize(
                params["date_debut"],
                params["date_fin"],
            )
        )


class RentabiliteProjetView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "paie"
    service = cout_projet_service

    def get(self, request):
        serializer = RentabiliteProjetQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data
        response = Response(self.service.simulate(
            params["date_debut"], params["date_fin"], params["projet"], params["chiffre_affaires"],
        ))
        response["Cache-Control"] = "private, no-store"
        return response
