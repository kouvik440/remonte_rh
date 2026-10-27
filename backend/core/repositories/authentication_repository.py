from typing import List, Optional

from django.contrib.auth import authenticate as django_authenticate

from core.interfaces.authentication_repository import AuthenticationRepositoryInterface
from core.models import Employe
from core.permission_codes import permission_code, permission_identity


class AuthenticationRepository(AuthenticationRepositoryInterface):
    def authenticate(self, email: str, password: str) -> Optional[Employe]:
        return django_authenticate(
            username=email.strip().lower(),
            password=password,
        )

    def get_role_names(self, employee: Employe) -> List[str]:
        return list(employee.roles.values_list("nom", flat=True))

    def get_permission_codes(self, employee: Employe) -> List[str]:
        permissions = {
            permission_code(permission)
            for role in employee.roles.prefetch_related("permissions__content_type")
            for permission in role.permissions.all()
        }
        return sorted(permissions)

    def has_role(self, employee: Employe, role_name: str) -> bool:
        return employee.roles.filter(nom__iexact=role_name).exists()

    def has_permission(self, employee: Employe, permission_code: str) -> bool:
        model_name, codename = permission_identity(permission_code)
        return employee.roles.filter(
            permissions__content_type__app_label="core",
            permissions__content_type__model=model_name,
            permissions__codename=codename,
        ).exists()
