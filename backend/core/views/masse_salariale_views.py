from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import HasResourceCrudPermission
from core.services.masse_salariale_export_service import masse_salariale_export_service
from core.services.masse_salariale_service import masse_salariale_service
from core.serializers.masse_salariale_serializer import (
    MasseSalarialeEvolutionQuerySerializer,
    MasseSalarialeExportQuerySerializer,
    MasseSalarialeQuerySerializer,
)


class MasseSalarialeView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "paie"
    service = masse_salariale_service

    def get(self, request):
        serializer = MasseSalarialeQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data
        return Response(
            self.service.summarize(
                params["periode_debut"],
                params["periode_fin"],
                department_id=params.get("departement"),
            )
        )


class MasseSalarialeEvolutionView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "paie"
    service = masse_salariale_service

    def get(self, request):
        serializer = MasseSalarialeEvolutionQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data
        return Response(
            self.service.evolution(
                params["periode_debut"],
                params["periode_fin"],
                granularity=params["granularite"],
                department_id=params.get("departement"),
            )
        )


class MasseSalarialeExportView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "paie"
    export_service = masse_salariale_export_service

    def get(self, request):
        serializer = MasseSalarialeExportQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data
        body, content_type, filename = self.export_service.export(
            params["periode_debut"],
            params["periode_fin"],
            params["format_fichier"],
            department_id=params.get("departement"),
            granularity=params["granularite"],
        )
        response = HttpResponse(body, content_type=content_type)
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response
