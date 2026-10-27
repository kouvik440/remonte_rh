from rest_framework.permissions import BasePermission

from core.services.authentication_service import authentication_service


class IsAdminRh(BasePermission):
    message = "Vous n'avez pas la permission ADMIN_RH."

    def has_permission(self, request, view):
        employee = request.user
        if not employee.is_authenticated:
            return False
        return authentication_service.has_role(employee, "ADMIN_RH")


class HasActionPermission(BasePermission):
    message = "Votre rôle ne possède pas la permission requise pour cette action."
    action_permissions = {}

    def has_permission(self, request, view):
        employee = request.user
        if not employee.is_authenticated:
            return False

        permission_code = self.action_permissions.get(request.method)
        return bool(
            permission_code
            and authentication_service.has_permission(employee, permission_code)
        )


class HasResourceCrudPermission(BasePermission):
    message = "Votre rôle ne possède pas la permission requise pour cette action."
    permission_resource = None
    action_names = {
        "GET": "read",
        "HEAD": "read",
        "OPTIONS": "read",
        "POST": "create",
        "PUT": "update",
        "PATCH": "update",
        "DELETE": "delete",
    }

    def has_permission(self, request, view):
        employee = request.user
        if not employee.is_authenticated:
            return False
        resource = getattr(view, "permission_resource", self.permission_resource)
        action = self.action_names.get(request.method)
        if not resource or not action:
            return False
        return authentication_service.has_permission(employee, f"{resource}.{action}")


class HasDocumentAccess(HasResourceCrudPermission):
    permission_resource = "document"

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.method in {"GET", "HEAD", "OPTIONS"} or authentication_service.has_permission(
            request.user, "document.manage"
        )

    def has_object_permission(self, request, view, obj):
        if authentication_service.has_permission(request.user, "document.manage"):
            return True
        from core.services.document_service import document_service
        return document_service.belongs_to(obj.pk, request.user.pk)


class HasDocumentEmployeeAccess(HasDocumentAccess):
    permission_resource = "document_employe"

    def has_object_permission(self, request, view, obj):
        return obj.employe_id == request.user.pk or authentication_service.has_permission(
            request.user, "document.manage"
        )


class HasDemandeAbsenceAccess(HasResourceCrudPermission):
    permission_resource = "demande_absence"

    def has_object_permission(self, request, view, obj):
        if obj.employe_id == request.user.pk:
            return True
        return authentication_service.has_permission(
            request.user,
            "demande_absence.update",
        )


class HasDemandeAbsenceDecisionPermission(HasActionPermission):
    action_permissions = {
        "POST": "demande_absence.update",
    }


class HasFeuilleTempsDecisionPermission(HasActionPermission):
    action_permissions = {
        "GET": "feuille_temps.decide",
        "HEAD": "feuille_temps.decide",
        "OPTIONS": "feuille_temps.decide",
        "POST": "feuille_temps.decide",
    }


class HasPaieCalculationPermission(HasActionPermission):
    action_permissions = {
        "POST": "paie.update",
    }


class HasOrdreVirementDecisionPermission(HasActionPermission):
    action_permissions = {"POST": "ordre_virement.update"}


class HasTransferDocumentPermission(BasePermission):
    message = "Les droits de consultation des ordres et des paies ainsi que de génération du document sont requis."

    def has_permission(self, request, view):
        return request.user.is_authenticated and all(
            authentication_service.has_permission(request.user, code)
            for code in ("ordre_virement.read", "paie.read", "ordre_virement.generate_document")
        )


class HasPaieBulletinGenerationPermission(HasActionPermission):
    action_permissions = {"POST": "paie.update"}


class HasProjectAssignmentPermission(HasActionPermission):
    action_permissions = {
        "GET": "projet.read",
        "HEAD": "projet.read",
        "OPTIONS": "projet.read",
        "POST": "projet.assign_employees",
        "DELETE": "projet.assign_employees",
    }


class HasCoordonneesBancairesAccess(HasResourceCrudPermission):
    permission_resource = "coordonnees_bancaires"

    def has_object_permission(self, request, view, obj):
        if obj.employe_id == request.user.pk:
            return True
        return authentication_service.has_permission(
            request.user,
            "coordonnees_bancaires.manage",
        )


class HasRoleCrudPermission(HasActionPermission):
    action_permissions = {
        "GET": "role.read",
        "HEAD": "role.read",
        "OPTIONS": "role.read",
        "POST": "role.create",
        "PUT": "role.update",
        "PATCH": "role.update",
        "DELETE": "role.delete",
    }


class HasPermissionCrudPermission(HasActionPermission):
    action_permissions = {
        "GET": "permission.read",
        "HEAD": "permission.read",
        "OPTIONS": "permission.read",
        "POST": "permission.create",
        "PUT": "permission.update",
        "PATCH": "permission.update",
        "DELETE": "permission.delete",
    }

class HasRoleAssignmentPermission(HasActionPermission):
    action_permissions = {
        "POST": "role.assign_permissions",
        "DELETE": "role.assign_permissions",
    }


class HasEmployeeCrudPermission(BasePermission):
    message = "Votre rôle ne possède pas la permission requise pour cette action."
    action_permissions = {
        "GET": "employe.read",
        "HEAD": "employe.read",
        "OPTIONS": "employe.read",
        "POST": "employe.create",
        "PUT": "employe.update",
        "PATCH": "employe.update",
        "DELETE": "employe.delete",
    }

    def has_permission(self, request, view):
        employee = request.user
        if not employee.is_authenticated:
            return False
        permission_code = self.action_permissions.get(request.method)
        return bool(
            permission_code
            and authentication_service.has_permission(employee, permission_code)
        )


class HasEmployeeRoleAssignmentPermission(HasActionPermission):
    action_permissions = {
        "POST": "employe.assign_roles",
        "DELETE": "employe.assign_roles",
    }
