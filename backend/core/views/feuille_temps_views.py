from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import FeuilleTemps
from core.permissions import HasFeuilleTempsDecisionPermission
from core.serializers.feuille_temps_serializer import (
    FeuilleTempsRefusSerializer,
    FeuilleTempsQuerySerializer,
    FeuilleTempsProjectOptionSerializer,
    FeuilleTempsProjectQuerySerializer,
    FeuilleTempsSerializer,
    FeuilleTempsWriteSerializer,
)
from core.services.feuille_temps_service import feuille_temps_service


class FeuilleTempsListView(APIView):
    permission_classes = [IsAuthenticated]
    service = feuille_temps_service

    def get(self, request):
        query_serializer = FeuilleTempsQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        sheets = self.service.for_employee(
            request.user.pk,
            week_start=query_serializer.validated_data.get("semaine_debut"),
            work_date=query_serializer.validated_data.get("date_travail"),
        )
        return Response(FeuilleTempsSerializer(sheets, many=True).data)

    def post(self, request):
        serializer = FeuilleTempsWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sheet = self.service.create(
            request.user.pk,
            serializer.validated_data["semaine_debut"],
            serializer.validated_data["lignes"],
        )
        return Response(
            FeuilleTempsSerializer(sheet).data,
            status=status.HTTP_201_CREATED,
        )


class FeuilleTempsProjectOptionsView(APIView):
    permission_classes = [IsAuthenticated]
    service = feuille_temps_service

    def get(self, request):
        query = FeuilleTempsProjectQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        projects = self.service.active_projects_for_employee(request.user.pk, pending_only=query.validated_data["a_saisir"])
        response = Response(FeuilleTempsProjectOptionSerializer(projects, many=True).data)
        response["Cache-Control"] = "private, no-store"
        return response


class FeuilleTempsDetailView(APIView):
    permission_classes = [IsAuthenticated]
    service = feuille_temps_service

    def get(self, request, feuille_id):
        try:
            sheet = self.service.get_for_employee(feuille_id, request.user.pk)
        except FeuilleTemps.DoesNotExist:
            return Response(
                {"detail": "Feuille de temps non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(FeuilleTempsSerializer(sheet).data)

    def put(self, request, feuille_id):
        try:
            sheet = self.service.get_for_employee(feuille_id, request.user.pk)
        except FeuilleTemps.DoesNotExist:
            return Response(
                {"detail": "Feuille de temps non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = FeuilleTempsWriteSerializer(sheet, data=request.data)
        serializer.is_valid(raise_exception=True)
        sheet = self.service.update(
            feuille_id,
            request.user.pk,
            serializer.validated_data["semaine_debut"],
            serializer.validated_data["lignes"],
        )
        return Response(FeuilleTempsSerializer(sheet).data)

    def delete(self, request, feuille_id):
        try:
            self.service.delete(feuille_id, request.user.pk)
        except FeuilleTemps.DoesNotExist:
            return Response(
                {"detail": "Feuille de temps non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class FeuilleTempsSoumettreView(APIView):
    permission_classes = [IsAuthenticated]
    service = feuille_temps_service

    def post(self, request, feuille_id):
        try:
            sheet = self.service.submit(feuille_id, request.user.pk)
        except FeuilleTemps.DoesNotExist:
            return Response(
                {"detail": "Feuille de temps non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(FeuilleTempsSerializer(sheet).data)


class FeuilleTempsAValiderView(APIView):
    permission_classes = [HasFeuilleTempsDecisionPermission]
    service = feuille_temps_service

    def get(self, request):
        sheets = self.service.submitted_for_decision()
        return Response(FeuilleTempsSerializer(sheets, many=True).data)


class FeuilleTempsDecisionView(APIView):
    permission_classes = [HasFeuilleTempsDecisionPermission]
    service = feuille_temps_service

    def post(self, request, feuille_id, action):
        try:
            if action == "valider":
                sheet = self.service.approve(feuille_id, request.user.pk)
            else:
                serializer = FeuilleTempsRefusSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                sheet = self.service.reject(
                    feuille_id,
                    request.user.pk,
                    serializer.validated_data["motif"],
                )
        except FeuilleTemps.DoesNotExist:
            return Response(
                {"detail": "Feuille de temps non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(FeuilleTempsSerializer(sheet).data)
