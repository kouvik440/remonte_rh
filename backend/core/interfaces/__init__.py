from .authentication_repository import AuthenticationRepositoryInterface
from .contrat_repository import ContratRepositoryInterface
from .contrat_type_contrat_repository import ContratTypeContratRepositoryInterface
from .coordonnees_bancaires_repository import CoordonneesBancairesRepositoryInterface
from .demande_absence_repository import DemandeAbsenceRepositoryInterface
from .departement_repository import DepartementRepositoryInterface
from .document_employe_repository import DocumentEmployeRepositoryInterface
from .document_repository import DocumentRepositoryInterface
from .employe_repository import EmployeRepositoryInterface
from .ordre_virement_repository import OrdreVirementRepositoryInterface
from .paie_repository import PaieRepositoryInterface
from .poste_repository import PosteRepositoryInterface
from .role_repository import PermissionRepositoryInterface, RoleRepositoryInterface
from .type_contrat_repository import TypeContratRepositoryInterface
from .type_document_repository import TypeDocumentRepositoryInterface

__all__ = [
	"AuthenticationRepositoryInterface",
	"ContratRepositoryInterface",
	"ContratTypeContratRepositoryInterface",
	"CoordonneesBancairesRepositoryInterface",
	"DemandeAbsenceRepositoryInterface",
	"DepartementRepositoryInterface",
	"DocumentEmployeRepositoryInterface",
	"DocumentRepositoryInterface",
	"EmployeRepositoryInterface",
	"OrdreVirementRepositoryInterface",
	"PaieRepositoryInterface",
	"PermissionRepositoryInterface",
	"PosteRepositoryInterface",
	"RoleRepositoryInterface",
	"TypeContratRepositoryInterface",
	"TypeDocumentRepositoryInterface",
]
