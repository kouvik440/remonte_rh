from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import AffectationProjet, Projet, TacheProjet
from core.permissions import (
    HasProjectAssignmentPermission,
    HasResourceCrudPermission,
)
from core.serializers.projet_serializer import (
    AffectationEmployeRequestSerializer,
    AffectationProjetSerializer,
    ProjetSerializer,
    TacheProjetSerializer,
)
from core.services.projet_service import projet_service


class ProjetListView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "projet"
    service = projet_service

    def get(self, request):
        return Response(ProjetSerializer(self.service.get_all_projects(), many=True).data)

    def post(self, request):
        serializer = ProjetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = self.service.create_project(serializer.validated_data)
        return Response(ProjetSerializer(project).data, status=status.HTTP_201_CREATED)


class ProjetDetailView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "projet"
    service = projet_service

    def get(self, request, projet_id):
        try:
            project = self.service.get_project(projet_id)
        except Projet.DoesNotExist:
            return Response({"detail": "Projet non trouvé."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ProjetSerializer(project).data)

    def put(self, request, projet_id):
        try:
            project = self.service.get_project(projet_id)
        except Projet.DoesNotExist:
            return Response({"detail": "Projet non trouvé."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProjetSerializer(project, data=request.data)
        serializer.is_valid(raise_exception=True)
        project = self.service.update_project(projet_id, serializer.validated_data)
        return Response(ProjetSerializer(project).data)

    def delete(self, request, projet_id):
        try:
            self.service.delete_project(projet_id)
        except Projet.DoesNotExist:
            return Response({"detail": "Projet non trouvé."}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TacheProjetListView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "tache"
    service = projet_service

    def get(self, request, projet_id):
        try:
            tasks = self.service.get_tasks(projet_id)
        except Projet.DoesNotExist:
            return Response({"detail": "Projet non trouvé."}, status=status.HTTP_404_NOT_FOUND)
        return Response(TacheProjetSerializer(tasks, many=True).data)

    def post(self, request, projet_id):
        try:
            self.service.get_project(projet_id)
        except Projet.DoesNotExist:
            return Response({"detail": "Projet non trouvé."}, status=status.HTTP_404_NOT_FOUND)
        serializer = TacheProjetSerializer(
            data=request.data,
            context={"projet_id": projet_id},
        )
        serializer.is_valid(raise_exception=True)
        task = self.service.create_task(projet_id, serializer.validated_data)
        return Response(TacheProjetSerializer(task).data, status=status.HTTP_201_CREATED)


class TacheProjetDetailView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "tache"
    service = projet_service

    def get(self, request, projet_id, tache_id):
        try:
            task = self._get_project_task(projet_id, tache_id)
        except (Projet.DoesNotExist, TacheProjet.DoesNotExist):
            return Response({"detail": "Tâche non trouvée."}, status=status.HTTP_404_NOT_FOUND)
        return Response(TacheProjetSerializer(task).data)

    def put(self, request, projet_id, tache_id):
        try:
            task = self._get_project_task(projet_id, tache_id)
        except (Projet.DoesNotExist, TacheProjet.DoesNotExist):
            return Response({"detail": "Tâche non trouvée."}, status=status.HTTP_404_NOT_FOUND)
        serializer = TacheProjetSerializer(
            task,
            data=request.data,
            context={"projet_id": projet_id},
        )
        serializer.is_valid(raise_exception=True)
        task = self.service.update_task(tache_id, serializer.validated_data)
        return Response(TacheProjetSerializer(task).data)

    def delete(self, request, projet_id, tache_id):
        try:
            task = self._get_project_task(projet_id, tache_id)
            self.service.delete_task(task.pk)
        except (Projet.DoesNotExist, TacheProjet.DoesNotExist):
            return Response({"detail": "Tâche non trouvée."}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _get_project_task(self, projet_id, tache_id):
        self.service.get_project(projet_id)
        task = self.service.get_task(tache_id)
        if task.projet_id != projet_id:
            raise TacheProjet.DoesNotExist
        return task


class AffectationProjetListView(APIView):
    permission_classes = [HasProjectAssignmentPermission]
    service = projet_service

    def get(self, request, projet_id, employe_id=None):
        try:
            assignments = self.service.get_assignments(
                projet_id,
                employee_id=employe_id,
            )
        except Projet.DoesNotExist:
            return Response({"detail": "Projet non trouvé."}, status=status.HTTP_404_NOT_FOUND)
        if employe_id is not None:
            try:
                assignment = assignments.get()
            except AffectationProjet.DoesNotExist:
                return Response({"detail": "Affectation non trouvée."}, status=status.HTTP_404_NOT_FOUND)
            return Response(AffectationProjetSerializer(assignment).data)
        return Response(AffectationProjetSerializer(assignments, many=True).data)

    def post(self, request, projet_id):
        serializer = AffectationEmployeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            assignment = self.service.assign_employee(
                projet_id,
                serializer.validated_data["employe"].pk,
            )
        except Projet.DoesNotExist:
            return Response({"detail": "Projet non trouvé."}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError:
            return Response(
                {"employe": "Cet employé est déjà affecté à ce projet."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(
            AffectationProjetSerializer(assignment).data,
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request, projet_id, employe_id=None):
        if employe_id is None:
            return Response(
                {"employe": "L'identifiant de l'employé est requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            self.service.remove_assignment(projet_id, employe_id)
        except Projet.DoesNotExist:
            return Response({"detail": "Projet non trouvé."}, status=status.HTTP_404_NOT_FOUND)
        except AffectationProjet.DoesNotExist:
            return Response({"detail": "Affectation non trouvée."}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
