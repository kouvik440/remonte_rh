from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import DemandeAbsence
from core.permissions import (
    HasDemandeAbsenceAccess,
    HasDemandeAbsenceDecisionPermission,
)
from core.services.authentication_service import authentication_service
from core.services.demande_absence_service import demande_absence_service
from core.services.planning_service import planning_service
from core.serializers.demande_absence_serializer import (
    DemandeAbsenceDetailSerializer,
    DemandeAbsenceSerializer,
    PlanningEventQuerySerializer,
    PlanningEventSerializer,
)


class PlanningEventsListView(APIView):
    permission_classes = [HasDemandeAbsenceAccess]
    service = planning_service

    def get(self, request):
        query_serializer = PlanningEventQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        filters = query_serializer.validated_data
        can_view_all = authentication_service.has_permission(
            request.user,
            "demande_absence.update",
        )
        employee_id = filters.get("employe")
        if not can_view_all:
            employee_id = request.user.pk
        events = self.service.get_events(
            filters["date_debut"],
            filters["date_fin"],
            department_id=filters.get("departement"),
            employee_id=employee_id,
        )
        return Response(PlanningEventSerializer(events, many=True).data)


class DemandeAbsenceListView(APIView):
    permission_classes = [HasDemandeAbsenceAccess]
    service = demande_absence_service

    def get(self, request):
        if authentication_service.has_permission(request.user, "demande_absence.update"):
            demandes = self.service.get_all()
        else:
            demandes = self.service.get_for_employee(request.user.pk)
        return Response(DemandeAbsenceSerializer(demandes, many=True).data)

    def post(self, request):
        serializer = DemandeAbsenceSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = dict(serializer.validated_data)
        data["employe"] = request.user
        demande_absence = self.service.create(data)
        return Response(DemandeAbsenceSerializer(demande_absence).data, status=status.HTTP_201_CREATED)


class DemandeAbsenceDetailView(APIView):
    permission_classes = [HasDemandeAbsenceAccess]
    service = demande_absence_service

    def get(self, request, demande_absence_id):
        try:
            demande_absence = self.service.get(demande_absence_id)
        except DemandeAbsence.DoesNotExist:
            return Response({"detail": "Demande d'absence non trouvée"}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, demande_absence)
        return Response(DemandeAbsenceDetailSerializer(demande_absence).data)

    def put(self, request, demande_absence_id):
        try:
            demande_absence = self.service.get(demande_absence_id)
        except DemandeAbsence.DoesNotExist:
            return Response({"detail": "Demande d'absence non trouvée"}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, demande_absence)
        serializer = DemandeAbsenceSerializer(demande_absence, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        demande_absence = self.service.update(demande_absence_id, serializer.validated_data)
        return Response(DemandeAbsenceSerializer(demande_absence).data)

    def delete(self, request, demande_absence_id):
        try:
            demande_absence = self.service.get(demande_absence_id)
        except DemandeAbsence.DoesNotExist:
            return Response({"detail": "Demande d'absence non trouvée"}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, demande_absence)
        self.service.delete(demande_absence_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DemandeAbsenceValiderView(APIView):
    permission_classes = [HasDemandeAbsenceDecisionPermission]
    service = demande_absence_service

    def post(self, request, demande_absence_id):
        try:
            demande = self.service.approve(demande_absence_id, request.user.pk)
        except DemandeAbsence.DoesNotExist:
            return Response(
                {"detail": "Demande d'absence non trouvée"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(DemandeAbsenceSerializer(demande).data)


class DemandeAbsenceRefuserView(APIView):
    permission_classes = [HasDemandeAbsenceDecisionPermission]
    service = demande_absence_service

    def post(self, request, demande_absence_id):
        try:
            demande = self.service.reject(demande_absence_id, request.user.pk)
        except DemandeAbsence.DoesNotExist:
            return Response(
                {"detail": "Demande d'absence non trouvée"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(DemandeAbsenceSerializer(demande).data)
