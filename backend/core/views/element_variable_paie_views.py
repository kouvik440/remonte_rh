from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import ElementVariablePaie
from core.permissions import HasPaieCalculationPermission, HasResourceCrudPermission
from core.serializers.element_variable_paie_serializer import (
    ElementVariablePaieSerializer,
    ElementVariablePaieQuerySerializer,
)
from core.services.element_variable_paie_service import (
    element_variable_paie_service,
)


class ElementVariablePaieListView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "paie"
    service = element_variable_paie_service

    def get(self, request):
        filters = ElementVariablePaieQuerySerializer(data=request.query_params)
        filters.is_valid(raise_exception=True)
        elements = self.service.filtered(
            employee_id=filters.validated_data.get("employe"),
            periode=filters.validated_data.get("periode"),
        )
        return Response(ElementVariablePaieSerializer(elements, many=True).data)

    def post(self, request):
        serializer = ElementVariablePaieSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        element = self.service.create(serializer.validated_data)
        return Response(
            ElementVariablePaieSerializer(element).data,
            status=status.HTTP_201_CREATED,
        )


class ElementVariablePaieDetailView(APIView):
    permission_classes = [HasResourceCrudPermission]
    permission_resource = "paie"
    service = element_variable_paie_service

    def get(self, request, element_id):
        try:
            element = self.service.get(element_id)
        except ElementVariablePaie.DoesNotExist:
            return Response({"detail": "Élément variable non trouvé"}, status=404)
        return Response(ElementVariablePaieSerializer(element).data)

    def put(self, request, element_id):
        try:
            element = self.service.get(element_id)
        except ElementVariablePaie.DoesNotExist:
            return Response({"detail": "Élément variable non trouvé"}, status=404)
        serializer = ElementVariablePaieSerializer(element, data=request.data)
        serializer.is_valid(raise_exception=True)
        element = self.service.update(element_id, serializer.validated_data)
        return Response(ElementVariablePaieSerializer(element).data)

    def delete(self, request, element_id):
        try:
            self.service.delete(element_id)
        except ElementVariablePaie.DoesNotExist:
            return Response({"detail": "Élément variable non trouvé"}, status=404)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ElementVariablePaieValiderView(APIView):
    permission_classes = [HasPaieCalculationPermission]
    service = element_variable_paie_service

    def post(self, request, element_id):
        try:
            element = self.service.validate(element_id)
        except ElementVariablePaie.DoesNotExist:
            return Response({"detail": "Élément variable non trouvé"}, status=404)
        return Response(ElementVariablePaieSerializer(element).data)