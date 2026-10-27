from abc import ABC, abstractmethod
from typing import List, Optional

from core.models import Employe


class AuthenticationRepositoryInterface(ABC):
    @abstractmethod
    def authenticate(self, email: str, password: str) -> Optional[Employe]:
        raise NotImplementedError

    @abstractmethod
    def get_role_names(self, employee: Employe) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    def get_permission_codes(self, employee: Employe) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    def has_role(self, employee: Employe, role_name: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def has_permission(self, employee: Employe, permission_code: str) -> bool:
        raise NotImplementedError
