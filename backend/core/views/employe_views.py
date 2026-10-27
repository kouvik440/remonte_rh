from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.services.employe_service import employe_service
from core.models import Employe, Role, EmployeHistorique
from core.permissions import (
    HasEmployeeCrudPermission,
    HasEmployeeRoleAssignmentPermission,
)
from core.services.authentication_service import authentication_service
from core.serializers.employe_serializer import (
    EmployeeRoleSerializer,
    EmployeSerializer,
    EmployeWriteSerializer,
    EmployeQuerySerializer,
    EmployeHistoriqueSerializer,
)


class EmployeListView(APIView):
    permission_classes = [HasEmployeeCrudPermission]
    service = employe_service

    def get(self, request):
        query = EmployeQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        return Response(EmployeSerializer(self.service.get_all(**query.validated_data), many=True).data)

    def post(self, request):
        serializer = EmployeWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        if not authentication_service.has_permission(request.user, "employe.assign_roles"):
            data.pop("roles", None)
        try:
            employee = self.service.create(data, actor=request.user)
        except Role.DoesNotExist:
            return Response(
                {"roles": ["Un ou plusieurs rôles indiqués n'existent pas."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(EmployeSerializer(employee).data, status=status.HTTP_201_CREATED)


class EmployeDetailView(APIView):
    permission_classes = [HasEmployeeCrudPermission]
    service = employe_service

    def get(self, request, employee_id):
        try:
            return Response(EmployeSerializer(self.service.get(employee_id)).data)
        except Employe.DoesNotExist:
            return Response({"detail": "Employé non trouvé"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, employee_id):
        try:
            serializer = EmployeWriteSerializer(
                self.service.get(employee_id),
                data=request.data,
            )
        except Employe.DoesNotExist:
            return Response({"detail": "Employé non trouvé"}, status=status.HTTP_404_NOT_FOUND)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        if not authentication_service.has_permission(request.user, "employe.assign_roles"):
            data.pop("roles", None)
        try:
            employee = self.service.update(employee_id, data, actor=request.user)
        except Role.DoesNotExist:
            return Response(
                {"roles": ["Un ou plusieurs rôles indiqués n'existent pas."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(EmployeSerializer(employee).data)

    def delete(self, request, employee_id):
        try:
            self.service.delete(employee_id)
        except Employe.DoesNotExist:
            return Response({"detail": "Employé non trouvé"}, status=status.HTTP_404_NOT_FOUND)
        except Role.DoesNotExist:
            return Response(
                {"role_ids": ["Un ou plusieurs rôles indiqués n'existent pas."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmployeeHistoryView(APIView):
    permission_classes = [HasEmployeeCrudPermission]

    def get(self, request, employee_id):
        if not Employe.objects.filter(pk=employee_id).exists():
            return Response({"detail": "Employé non trouvé"}, status=status.HTTP_404_NOT_FOUND)
        events = EmployeHistorique.objects.filter(employe_id=employee_id)
        if not authentication_service.has_permission(request.user, "contrat.read"):
            events = events.exclude(categorie="CONTRAT")
        response = Response(EmployeHistoriqueSerializer(events, many=True).data)
        response["Cache-Control"] = "private, no-store"
        return response


class EmployeeRoleView(APIView):
    permission_classes = [HasEmployeeRoleAssignmentPermission]
    service = employe_service

    def post(self, request, employee_id):
        try:
            serializer = EmployeeRoleSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            employee = self.service.add_roles(
                employee_id,
                serializer.validated_data["role_ids"],
            )
            return Response(EmployeSerializer(employee).data)
        except Employe.DoesNotExist:
            return Response({"detail": "Employé non trouvé"}, status=status.HTTP_404_NOT_FOUND)
        except Role.DoesNotExist:
            return Response(
                {"role_ids": ["Un ou plusieurs rôles indiqués n'existent pas."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def delete(self, request, employee_id):
        try:
            serializer = EmployeeRoleSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            employee = self.service.remove_roles(
                employee_id,
                serializer.validated_data["role_ids"],
            )
            return Response(EmployeSerializer(employee).data)
        except Employe.DoesNotExist:
            return Response({"detail": "Employé non trouvé"}, status=status.HTTP_404_NOT_FOUND)
