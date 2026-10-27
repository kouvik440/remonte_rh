from django.urls import path

from core.views.authentication_views import CurrentUserView, LoginView, RefreshView, ChangePasswordView
from core.views.conge_views import (
    TypeCongeDetailView,
    TypeCongeListView,
)
from core.views.contrat_type_contrat_views import (
    ContratTypeContratDetailView,
    ContratTypeContratListView,
)
from core.views.contrat_views import ContratDetailView, ContratListView
from core.views.cout_projet_views import CoutProjetView, RentabiliteProjetView
from core.views.tgm_views import TgmListView
from core.views.coordonnees_bancaires_views import (
    CoordonneesBancairesDetailView,
    CoordonneesBancairesListView,
)
from core.views.demande_absence_views import (
    DemandeAbsenceDetailView,
    DemandeAbsenceListView,
    DemandeAbsenceRefuserView,
    DemandeAbsenceValiderView,
    PlanningEventsListView,
)
from core.views.departement_views import DepartementDetailView, DepartementListView
from core.views.document_employe_views import DocumentEmployeDetailView, DocumentEmployeListView
from core.views.document_views import DocumentDetailView, DocumentListView
from core.views.feuille_temps_views import (
    FeuilleTempsAValiderView,
    FeuilleTempsDecisionView,
    FeuilleTempsDetailView,
    FeuilleTempsListView,
    FeuilleTempsProjectOptionsView,
    FeuilleTempsSoumettreView,
)
from core.views.element_variable_paie_views import (
    ElementVariablePaieDetailView,
    ElementVariablePaieListView,
    ElementVariablePaieValiderView,
)
from core.views.employe_views import (
    EmployeeHistoryView,
    EmployeeRoleView,
    EmployeDetailView,
    EmployeListView,
)
from core.views.ordre_virement_views import OrdreVirementActionView, OrdreVirementDetailView, OrdreVirementListView
from core.views.paie_views import (
    PersonalPayslipListView,
    PaieAnnulerView,
    PaieBulletinView,
    PaieCalculerView,
    PaieDetailView,
    PaieListView,
    PaieMarquerPayeeView,
    PaieValiderView,
)
from core.views.masse_salariale_views import (
    MasseSalarialeEvolutionView,
    MasseSalarialeExportView,
    MasseSalarialeView,
)
from core.views.poste_views import PosteDetailView, PosteListView
from core.views.payroll_contract_views import PayrollContractContextView
from core.views.transfer_document_views import TransferDocumentContextView, TransferDocumentView
from core.views.projet_views import (
    AffectationProjetListView,
    ProjetDetailView,
    ProjetListView,
    TacheProjetDetailView,
    TacheProjetListView,
)
from core.views.role_views import (
    PermissionDetailView,
    PermissionListView,
    RoleDetailView,
    RoleListView,
    RolePermissionView,
)
from core.views.regle_paie_views import (
    ReglePaieDetailView,
    ReglePaieListView,
    ReglePaieValiderView,
)
from core.views.solde_conge_views import SoldeCongeDetailView, SoldeCongeListView
from core.views.type_contrat_views import TypeContratDetailView, TypeContratListView
from core.views.type_document_views import TypeDocumentDetailView, TypeDocumentListView

urlpatterns = [
    path("analyses/couts-projets/simulation/", RentabiliteProjetView.as_view(), name="rentabilite-projet"),
    path("analyses/tgm/", TgmListView.as_view(), name="tgm-list"),
    path("analyses/couts-projets/", CoutProjetView.as_view(), name="couts-projets"),
    path("analyses/masse-salariale/export/", MasseSalarialeExportView.as_view(), name="masse-salariale-export"),
    path("analyses/masse-salariale/evolution/", MasseSalarialeEvolutionView.as_view(), name="masse-salariale-evolution"),
    path("analyses/masse-salariale/", MasseSalarialeView.as_view(), name="masse-salariale"),
    path("conges/types/", TypeCongeListView.as_view(), name="conge-type-list"),
    path(
        "conges/types/<int:type_conge_id>/",
        TypeCongeDetailView.as_view(),
        name="conge-type-detail",
    ),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/me/", CurrentUserView.as_view(), name="auth-current-user"),
    path("auth/password/", ChangePasswordView.as_view(), name="auth-change-password"),
    path("auth/refresh/", RefreshView.as_view(), name="auth-refresh"),
    path("departements/", DepartementListView.as_view(), name="departement-list"),
    path("departements/<int:department_id>/", DepartementDetailView.as_view(), name="departement-detail"),
    path("postes/", PosteListView.as_view(), name="poste-list"),
    path("postes/<int:poste_id>/", PosteDetailView.as_view(), name="poste-detail"),
    path("projets/", ProjetListView.as_view(), name="projet-list"),
    path("projets/<int:projet_id>/", ProjetDetailView.as_view(), name="projet-detail"),
    path(
        "projets/<int:projet_id>/taches/",
        TacheProjetListView.as_view(),
        name="projet-tache-list",
    ),
    path(
        "projets/<int:projet_id>/taches/<int:tache_id>/",
        TacheProjetDetailView.as_view(),
        name="projet-tache-detail",
    ),
    path(
        "projets/<int:projet_id>/affectations/",
        AffectationProjetListView.as_view(),
        name="projet-affectation-list",
    ),
    path(
        "projets/<int:projet_id>/affectations/<int:employe_id>/",
        AffectationProjetListView.as_view(),
        name="projet-affectation-detail",
    ),
    path("types-contrat/", TypeContratListView.as_view(), name="type-contrat-list"),
    path("types-contrat/<int:type_contrat_id>/", TypeContratDetailView.as_view(), name="type-contrat-detail"),
    path("types-document/", TypeDocumentListView.as_view(), name="type-document-list"),
    path("types-document/<int:type_document_id>/", TypeDocumentDetailView.as_view(), name="type-document-detail"),
    path("contrats/", ContratListView.as_view(), name="contrat-list"),
    path("contrats/<int:contrat_id>/", ContratDetailView.as_view(), name="contrat-detail"),
    path("contrats-type/", ContratTypeContratListView.as_view(), name="contrat-type-list"),
    path("contrats-type/<int:contrat_type_contrat_id>/", ContratTypeContratDetailView.as_view(), name="contrat-type-detail"),
    path("coordonnees-bancaires/", CoordonneesBancairesListView.as_view(), name="coordonnees-bancaires-list"),
    path("coordonnees-bancaires/<int:coordonnees_bancaires_id>/", CoordonneesBancairesDetailView.as_view(), name="coordonnees-bancaires-detail"),
    path("demandes-absence/", DemandeAbsenceListView.as_view(), name="demande-absence-list"),
    path("demandes-absence/<int:demande_absence_id>/", DemandeAbsenceDetailView.as_view(), name="demande-absence-detail"),
    path("demandes-absence/<int:demande_absence_id>/valider/", DemandeAbsenceValiderView.as_view(), name="demande-absence-valider"),
    path("demandes-absence/<int:demande_absence_id>/refuser/", DemandeAbsenceRefuserView.as_view(), name="demande-absence-refuser"),
    path("feuilles-temps/", FeuilleTempsListView.as_view(), name="feuille-temps-list"),
    path("feuilles-temps/projets/", FeuilleTempsProjectOptionsView.as_view(), name="feuille-temps-projets"),
    path("feuilles-temps/a-valider/", FeuilleTempsAValiderView.as_view(), name="feuille-temps-a-valider"),
    path("feuilles-temps/<int:feuille_id>/", FeuilleTempsDetailView.as_view(), name="feuille-temps-detail"),
    path("feuilles-temps/<int:feuille_id>/soumettre/", FeuilleTempsSoumettreView.as_view(), name="feuille-temps-soumettre"),
    path("feuilles-temps/<int:feuille_id>/valider/", FeuilleTempsDecisionView.as_view(), {"action": "valider"}, name="feuille-temps-valider"),
    path("feuilles-temps/<int:feuille_id>/refuser/", FeuilleTempsDecisionView.as_view(), {"action": "refuser"}, name="feuille-temps-refuser"),
    path("planning/", PlanningEventsListView.as_view(), name="planning-events"),
    path("soldes-conge/", SoldeCongeListView.as_view(), name="solde-conge-list"),
    path("soldes-conge/<int:balance_id>/", SoldeCongeDetailView.as_view(), name="solde-conge-detail"),
    path("documents/", DocumentListView.as_view(), name="document-list"),
    path("documents/<int:document_id>/", DocumentDetailView.as_view(), name="document-detail"),
    path("documents-employe/", DocumentEmployeListView.as_view(), name="document-employe-list"),
    path("documents-employe/<int:document_employe_id>/", DocumentEmployeDetailView.as_view(), name="document-employe-detail"),
    path("ordres-virement/", OrdreVirementListView.as_view(), name="ordre-virement-list"),
    path("ordres-virement/<int:order_id>/document/contexte/", TransferDocumentContextView.as_view(), name="transfer-document-context"),
    path("ordres-virement/<int:order_id>/document/", TransferDocumentView.as_view(), name="transfer-document"),
    path("ordres-virement/<int:ordre_virement_id>/", OrdreVirementDetailView.as_view(), name="ordre-virement-detail"),
    path("ordres-virement/<int:ordre_virement_id>/traiter/", OrdreVirementActionView.as_view(), {"action": "traiter"}, name="ordre-virement-traiter"),
    path("ordres-virement/<int:ordre_virement_id>/rejeter/", OrdreVirementActionView.as_view(), {"action": "rejeter"}, name="ordre-virement-rejeter"),
    path("ordres-virement/<int:ordre_virement_id>/annuler/", OrdreVirementActionView.as_view(), {"action": "annuler"}, name="ordre-virement-annuler"),
    path("paiements/", PaieListView.as_view(), name="paie-list"),
    path("mes-bulletins/", PersonalPayslipListView.as_view(), name="personal-payslip-list"),
    path("paiements/contexte-contrat/", PayrollContractContextView.as_view(), name="paie-contexte-contrat"),
    path("paiements/<int:paie_id>/calculer/", PaieCalculerView.as_view(), name="paie-calculer"),
    path("paiements/<int:paie_id>/valider/", PaieValiderView.as_view(), name="paie-valider"),
    path("paiements/<int:paie_id>/annuler/", PaieAnnulerView.as_view(), name="paie-annuler"),
    path("paiements/<int:paie_id>/marquer-payee/", PaieMarquerPayeeView.as_view(), name="paie-marquer-payee"),
    path("paiements/<int:paie_id>/bulletin/", PaieBulletinView.as_view(), name="paie-bulletin"),
    path("paiements/<int:paie_id>/", PaieDetailView.as_view(), name="paie-detail"),
    path("regles-paie/", ReglePaieListView.as_view(), name="regle-paie-list"),
    path("regles-paie/<int:regle_id>/valider/", ReglePaieValiderView.as_view(), name="regle-paie-valider"),
    path("regles-paie/<int:regle_id>/", ReglePaieDetailView.as_view(), name="regle-paie-detail"),
    path("elements-variables-paie/", ElementVariablePaieListView.as_view(), name="element-variable-paie-list"),
    path("elements-variables-paie/<int:element_id>/", ElementVariablePaieDetailView.as_view(), name="element-variable-paie-detail"),
    path("elements-variables-paie/<int:element_id>/valider/", ElementVariablePaieValiderView.as_view(), name="element-variable-paie-valider"),
    path("permissions/", PermissionListView.as_view(), name="permission-list"),
    path("permissions/<int:permission_id>/", PermissionDetailView.as_view(), name="permission-detail"),
    path("roles/", RoleListView.as_view(), name="role-list"),
    path("roles/<int:role_id>/", RoleDetailView.as_view(), name="role-detail"),
    path("roles/<int:role_id>/permissions/", RolePermissionView.as_view(), name="role-permissions"),
    path("employes/", EmployeListView.as_view(), name="employe-list"),
    path("employes/<int:employee_id>/", EmployeDetailView.as_view(), name="employe-detail"),
    path("employes/<int:employee_id>/historique/", EmployeeHistoryView.as_view(), name="employee-history"),
    path("employes/<int:employee_id>/roles/", EmployeeRoleView.as_view(), name="employee-roles"),
]
