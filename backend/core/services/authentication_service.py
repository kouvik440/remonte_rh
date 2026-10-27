from dataclasses import dataclass
from typing import List

from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from core.interfaces.authentication_repository import AuthenticationRepositoryInterface
from core.models import Employe
from core.repositories.authentication_repository import AuthenticationRepository


@dataclass(frozen=True)
class LoginResult:
    access: str
    refresh: str
    employee: Employe
    roles: List[str]
    permissions: List[str]


@dataclass(frozen=True)
class UserAccessSnapshot:
    employee: Employe
    roles: List[str]
    permissions: List[str]


@dataclass(frozen=True)
class TokenPair:
    access: str
    refresh: str


class AuthenticationService:
    def __init__(self, authentication_repository: AuthenticationRepositoryInterface):
        self.authentication_repository = authentication_repository

    def has_role(self, employee: Employe, role_name: str) -> bool:
        return self.authentication_repository.has_role(employee, role_name)

    def has_permission(self, employee: Employe, permission_code: str) -> bool:
        return self.authentication_repository.has_permission(employee, permission_code)

    def get_user_access_snapshot(self, employee: Employe) -> UserAccessSnapshot:
        return UserAccessSnapshot(
            employee=employee,
            roles=self.authentication_repository.get_role_names(employee),
            permissions=self.authentication_repository.get_permission_codes(employee),
        )

    def login(self, email: str, password: str) -> LoginResult:
        employee = self.authentication_repository.authenticate(email, password)
        if employee is None:
            raise AuthenticationFailed("Email ou mot de passe invalide.")
        if not employee.is_active:
            raise AuthenticationFailed("Le compte est inactif.")

        refresh = RefreshToken.for_user(employee)
        return LoginResult(
            access=str(refresh.access_token),
            refresh=str(refresh),
            employee=employee,
            roles=self.authentication_repository.get_role_names(employee),
            permissions=self.authentication_repository.get_permission_codes(employee),
        )

    def refresh(self, refresh_token: str) -> TokenPair:
        try:
            token = RefreshToken(refresh_token)
        except TokenError as error:
            raise AuthenticationFailed("Refresh token invalide.") from error

        return TokenPair(
            access=str(token.access_token),
            refresh=str(token),
        )


authentication_service = AuthenticationService(AuthenticationRepository())
