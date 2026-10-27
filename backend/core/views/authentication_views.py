from rest_framework import permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.services.authentication_service import authentication_service
from core.serializers.authentication_serializer import (
    LoginResponseSerializer,
    LoginSerializer,
    LoginUserResponseSerializer,
    RefreshRequestSerializer,
    RefreshResponseSerializer,
    CurrentUserUpdateSerializer,
    ChangePasswordSerializer,
)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = authentication_service.login(**serializer.validated_data)
        response_serializer = LoginResponseSerializer(instance=result)
        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        snapshot = authentication_service.get_user_access_snapshot(request.user)
        serializer = LoginUserResponseSerializer(instance=snapshot)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = CurrentUserUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(request.user, field, value)
        if serializer.validated_data:
            request.user.save(update_fields=list(serializer.validated_data))
        return self.get(request)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["nouveau_mot_de_passe"])
        request.user.save(update_fields=["password"])
        return Response({"detail": "Mot de passe modifié. Reconnectez-vous avec votre nouveau mot de passe."})


class RefreshView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RefreshRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = authentication_service.refresh(serializer.validated_data["refresh"])
        response_serializer = RefreshResponseSerializer(instance=result)
        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )
