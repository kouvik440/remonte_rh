from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import os
from unittest.mock import patch

from django.core.exceptions import ValidationError as DjangoValidationError
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import Permission as AuthPermission
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import (
    AffectationProjet,
    Contrat,
    CoordonneesBancaires,
    Departement,
    DemandeAbsence,
    Document,
    Employe,
    FeuilleTemps,
    LigneFeuilleTemps,
    OrdreVirement,
    Paie,
    Projet,
    ReglePaie,
    Role,
    SoldeConge,
    TacheProjet,
    TypeContrat,
    TypeConge,
    TypeDocument,
)
from core.permission_codes import (
    CORE_PERMISSION_MODELS,
    get_permission_by_code,
    permission_code,
)
from core.security import decrypt_bank_value, encrypt_bank_value, iban_fingerprint


class CrudPermissionCatalogTests(APITestCase):
    def test_employee_role_and_permission_codes_use_django_permissions(self):
        expected_codes = {
            f"{resource}.{action}"
            for resource in ("employe", "role", "permission")
            for action in ("read", "create", "update", "delete")
        }
        expected_codes.add("role.assign_permissions")
        permissions = AuthPermission.objects.filter(
            content_type__app_label="core",
            content_type__model__in=CORE_PERMISSION_MODELS,
        ).select_related("content_type")
        codes = {permission_code(permission) for permission in permissions}

        self.assertTrue(expected_codes.issubset(codes))
        role_read_permission = get_permission_by_code("role.read")
        self.assertEqual(role_read_permission.codename, "view_role")
        decision_permission = get_permission_by_code("feuille_temps.decide")
        self.assertEqual(
            permission_code(decision_permission),
            "feuille_temps.decide",
        )


class BankDataSecurityTests(APITestCase):
    def setUp(self):
        from cryptography.fernet import Fernet

        self.key_patch = patch.dict(
            os.environ,
            {"BANK_DATA_ENCRYPTION_KEY": Fernet.generate_key().decode("ascii")},
        )
        self.key_patch.start()
        self.addCleanup(self.key_patch.stop)

    def test_bank_value_round_trips_without_storing_plaintext(self):
        value = "FR7630006000011234567890189"

        encrypted = encrypt_bank_value(value)

        self.assertNotEqual(encrypted, value)
        self.assertEqual(decrypt_bank_value(encrypted), value)

    def test_iban_fingerprint_normalizes_spaces_and_case(self):
        spaced_iban = "fr76 3000 6000 0112 3456 7890 189"
        compact_iban = "FR7630006000011234567890189"

        self.assertEqual(
            iban_fingerprint(spaced_iban),
            iban_fingerprint(compact_iban),
        )

    def test_missing_key_is_rejected(self):
        with patch.dict(os.environ, {"BANK_DATA_ENCRYPTION_KEY_FILE": ""}, clear=True):
            with self.assertRaisesMessage(
                Exception,
                "Set BANK_DATA_ENCRYPTION_KEY before using bank data.",
            ):
                encrypt_bank_value("value")


class CorsHeadersTests(APITestCase):
    def test_localhost_frontend_has_cors_headers(self):
        response = self.client.options(
            "/api/auth/login/",
            HTTP_ORIGIN="http://localhost:3000",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Access-Control-Allow-Origin"], "http://localhost:3000")
        self.assertIn("POST", response["Access-Control-Allow-Methods"]) 


class LoginPermissionsTests(APITestCase):
    def test_login_returns_roles_and_permission_codes(self):
        employee = Employe.objects.create_user(
            email="permission-user@example.com",
            password="SecurePassword123!",
            matricule="LOGIN-001",
            nom="Test",
            prenom="User",
            date_naissance=date(1990, 1, 1),
            adresse="1 rue de Test",
            telephone="0600000000",
            num_secu_sociale="LOGIN-001",
            date_entree=date(2020, 1, 1),
        )
        role = Role.objects.create(nom="EMPLOYE_CREATE")
        role.permissions.add(get_permission_by_code("employe.create"))
        employee.roles.add(role)

        response = self.client.post(
            reverse("auth-login"),
            {"email": employee.email, "password": "SecurePassword123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["roles"], ["EMPLOYE_CREATE"])
        self.assertEqual(response.data["user"]["permissions"], ["employe.create"])

    def test_current_user_endpoint_returns_permissions_changed_after_login(self):
        employee = Employe.objects.create_user(
            email="current-user@example.com",
            password="SecurePassword123!",
            matricule="CURRENT-001",
            nom="Current",
            prenom="User",
            date_naissance=date(1990, 1, 1),
            adresse="1 rue de Test",
            telephone="0600000000",
            num_secu_sociale="CURRENT-001",
            date_entree=date(2020, 1, 1),
        )
        self.client.force_authenticate(user=employee)
        role = Role.objects.create(nom="CURRENT_USER_ROLE")
        role.permissions.add(get_permission_by_code("employe.delete"))
        employee.roles.add(role)

        response = self.client.get(reverse("auth-current-user"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["roles"], ["CURRENT_USER_ROLE"])
        self.assertEqual(response.data["permissions"], ["employe.delete"])


class RoleAccessPermissionTests(APITestCase):
    def setUp(self):
        role_read = Role.objects.create(nom="ROLE_VIEWER")
        role_read.permissions.add(get_permission_by_code("role.read"))
        self.employee = Employe.objects.create_user(
            email="role-viewer@example.com",
            password="SecurePassword123!",
            matricule="ROLE-VIEWER-001",
            nom="Viewer",
            prenom="Role",
            date_naissance=date(1990, 1, 1),
            adresse="1 rue de Test",
            telephone="0600000000",
            num_secu_sociale="ROLE-VIEWER-SSN",
            date_entree=date(2020, 1, 1),
        )
        self.employee.roles.add(role_read)
        self.client.force_authenticate(user=self.employee)

    def test_role_read_permission_allows_listing_roles(self):
        response = self.client.get(reverse("role-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_role_read_permission_allows_reading_permission_catalog(self):
        self.employee.roles.first().permissions.add(
            get_permission_by_code("permission.read")
        )
        response = self.client.get(reverse("permission-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_role_delete_permission_allows_deleting_assigned_role(self):
        self.employee.roles.first().permissions.add(
            get_permission_by_code("role.delete")
        )
        target = Role.objects.create(nom="ROLE_TO_DELETE")
        self.employee.roles.add(target)
        target_id = target.pk

        response = self.client.delete(reverse("role-detail", args=[target_id]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Role.objects.filter(pk=target_id).exists())
        self.assertFalse(self.employee.roles.filter(pk=target_id).exists())

    def test_role_read_permission_does_not_allow_deleting_roles(self):
        target = Role.objects.create(nom="PROTECTED_ROLE")

        response = self.client.delete(reverse("role-detail", args=[target.pk]))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Role.objects.filter(pk=target.pk).exists())

    def test_role_read_permission_does_not_allow_creating_roles(self):
        response = self.client.post(
            reverse("role-list"),
            {"nom": "UNAUTHORIZED_ROLE", "description": ""},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class EmployeCrudTests(APITestCase):
    def setUp(self):
        self.department = Departement.objects.create(
            nom="Développement",
            code="DEV",
        )
        self.admin_role = Role.objects.create(nom="ADMIN_RH")
        self.admin_role.permissions.set(
            AuthPermission.objects.filter(content_type__app_label="core")
        )
        self.admin_employee = self.create_employe(
            matricule="ADMIN-001",
            email="admin@example.com",
            num_secu_sociale="000000001",
            roles=[self.admin_role.pk],
        )
        self.client.force_authenticate(user=self.admin_employee)
        self.url = reverse("employe-list")

    def create_payload(self, **overrides):
        payload = {
            "matricule": "EM-001",
            "email": "employe@example.com",
            "password": "SecurePassword123!",
            "nom": "Dupont",
            "prenom": "Alexandre",
            "date_naissance": "1990-01-15",
            "adresse": "1 Rue de Paris",
            "telephone": "0612345678",
            "num_secu_sociale": "123456789",
            "date_entree": "2020-09-01",
            "date_sortie": None,
            "statut": "ACTIF",
            "is_active": True,
            "department": self.department.pk,
            "roles": [],
        }
        payload.update(overrides)
        return payload

    def create_employe(self, **overrides):
        payload = self.create_payload(**overrides)
        department_id = payload.pop("department")
        roles = payload.pop("roles", [])
        password = payload.pop("password")
        employee = Employe.objects.create_user(
            email=payload.pop("email"),
            password=password,
            is_active=payload.pop("is_active", True),
            department_id=department_id,
            **payload,
        )
        employee.roles.set(roles)
        return employee

    def test_create_employe(self):
        response = self.client.post(self.url, self.create_payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        employee = Employe.objects.get(pk=response.data["id"])
        self.assertEqual(employee.nom, "Dupont")
        self.assertTrue(employee.check_password("SecurePassword123!"))
        self.assertEqual(employee.department, self.department)

    def test_create_employe_with_unknown_role_returns_bad_request(self):
        response = self.client.post(
            self.url,
            self.create_payload(roles=[999999]),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("roles", response.data)
        self.assertFalse(Employe.objects.filter(email="employe@example.com").exists())

    def test_list_employes(self):
        self.create_employe(
            matricule="EM-002",
            email="second@example.com",
            num_secu_sociale="987654321",
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertIn("EM-002", [employee["matricule"] for employee in response.data])

    def test_retrieve_employe(self):
        employee = self.create_employe()

        response = self.client.get(reverse("employe-detail", args=[employee.pk]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], employee.email)
        self.assertNotIn("password_hash", response.data)
        self.assertNotIn("password", response.data)

    def test_update_employe(self):
        employee = self.create_employe()
        payload = self.create_payload(
            nom="Martin",
            date_sortie="2025-01-01",
            department=None,
        )

        response = self.client.put(
            reverse("employe-detail", args=[employee.pk]),
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        employee.refresh_from_db()
        self.assertEqual(employee.nom, "Martin")
        self.assertIsNone(employee.department)

    def test_delete_employe(self):
        employee = self.create_employe()

        response = self.client.delete(reverse("employe-detail", args=[employee.pk]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Employe.objects.filter(pk=employee.pk).exists())

    def test_invalid_date_range_is_rejected(self):
        payload = self.create_payload(
            date_entree="2025-01-02",
            date_sortie="2025-01-01",
        )

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("date_sortie", response.data)

    def test_create_permission_does_not_grant_read_permission(self):
        create_role = Role.objects.create(nom="EMPLOYE_CREATE")
        create_role.permissions.add(get_permission_by_code("employe.create"))
        creator = self.create_employe(
            matricule="CREATOR-001",
            email="creator@example.com",
            num_secu_sociale="000000002",
            roles=[create_role.pk],
        )
        self.client.force_authenticate(user=creator)

        create_response = self.client.post(self.url, self.create_payload(), format="json")
        read_response = self.client.get(self.url)

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(read_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_permission_cannot_assign_roles(self):
        create_role = Role.objects.create(nom="EMPLOYE_CREATE_ONLY")
        create_role.permissions.add(get_permission_by_code("employe.create"))
        creator = self.create_employe(
            matricule="CREATOR-002",
            email="creator2@example.com",
            num_secu_sociale="000000005",
            roles=[create_role.pk],
        )
        target_role = Role.objects.create(nom="ROLE_TO_ASSIGN")
        self.client.force_authenticate(user=creator)

        response = self.client.post(
            self.url,
            self.create_payload(roles=[target_role.pk]),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_employee = Employe.objects.get(pk=response.data["id"])
        self.assertFalse(created_employee.roles.exists())

    def test_delete_requires_delete_permission(self):
        read_role = Role.objects.create(nom="EMPLOYE_READ")
        read_role.permissions.add(get_permission_by_code("employe.read"))
        reader = self.create_employe(
            matricule="READER-001",
            email="reader@example.com",
            num_secu_sociale="000000003",
            roles=[read_role.pk],
        )
        target = self.create_employe(
            matricule="TARGET-001",
            email="target@example.com",
            num_secu_sociale="000000004",
        )
        self.client.force_authenticate(user=reader)

        delete_response = self.client.delete(
            reverse("employe-detail", args=[target.pk])
        )

        self.assertEqual(delete_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Employe.objects.filter(pk=target.pk).exists())


class DemandeAbsenceAccessTests(APITestCase):
    def setUp(self):
        self.employee = self.create_employee("OWNER-001", "owner@example.com", "ABS-SSN-001")
        self.other_employee = self.create_employee(
            "OTHER-001",
            "other@example.com",
            "ABS-SSN-002",
        )
        self.leave_type = TypeConge.objects.create(
            code="ABS-CP",
            libelle="Congé payé",
            jours_par_annee=25,
        )
        self.client.force_authenticate(user=self.employee)
        self.url = reverse("demande-absence-list")
        absence_role = Role.objects.create(nom="ABSENCE_EMPLOYEE")
        absence_role.permissions.add(
            get_permission_by_code("demande_absence.read"),
            get_permission_by_code("demande_absence.create"),
        )
        self.employee.roles.add(absence_role)

    def create_employee(self, matricule, email, social_security_number, role=None):
        employee = Employe.objects.create_user(
            email=email,
            password="SecurePassword123!",
            matricule=matricule,
            nom="Test",
            prenom="Employe",
            date_naissance=date(1990, 1, 1),
            adresse="1 rue de Test",
            telephone="0600000000",
            num_secu_sociale=social_security_number,
            date_entree=date(2020, 1, 1),
        )
        if role:
            employee.roles.add(role)
        return employee

    def create_demande(self, employee):
        return DemandeAbsence.objects.create(
            employe=employee,
            type_conge=self.leave_type,
            date_debut=date(2025, 5, 1),
            date_fin=date(2025, 5, 2),
            motif="Repos",
        )

    def test_request_list_identifies_employees_with_existing_visibility_rules(self):
        own_request = self.create_demande(self.employee)
        other_request = self.create_demande(self.other_employee)
        self.other_employee.prenom = "Awa"
        self.other_employee.nom = "Ouedraogo"
        self.other_employee.save(update_fields=["prenom", "nom"])

        personal_response = self.client.get(self.url)

        self.assertEqual(personal_response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in personal_response.data], [own_request.pk])
        self.assertEqual(personal_response.data[0]["employe_prenom"], self.employee.prenom)
        self.employee.roles.first().permissions.add(
            get_permission_by_code("demande_absence.update")
        )

        manager_response = self.client.get(self.url)

        self.assertEqual(manager_response.status_code, status.HTTP_200_OK)
        received = next(item for item in manager_response.data if item["id"] == other_request.pk)
        self.assertEqual(received["employe_prenom"], "Awa")
        self.assertEqual(received["employe_nom"], "Ouedraogo")
        self.assertNotIn("email", received)
        self.assertNotIn("num_secu_sociale", received)

    def test_request_detail_identifies_employee_and_department(self):
        department = Departement.objects.create(nom="Finance", code="DETAIL-FIN")
        self.employee.department = department
        self.employee.save(update_fields=["department"])
        demande = self.create_demande(self.employee)

        response = self.client.get(reverse("demande-absence-detail", args=[demande.pk]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["employe_nom"], self.employee.nom)
        self.assertEqual(response.data["employe_prenom"], self.employee.prenom)
        self.assertEqual(response.data["employe_matricule"], self.employee.matricule)
        self.assertEqual(response.data["departement_nom"], "Finance")
        self.assertEqual(response.data["motif"], "Repos")
        self.assertIsNone(response.data["valideur_nom"])
        self.assertNotIn("num_secu_sociale", response.data)

    def test_request_detail_handles_missing_department(self):
        demande = self.create_demande(self.employee)

        response = self.client.get(reverse("demande-absence-detail", args=[demande.pk]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["departement_nom"])

    def test_manager_can_read_other_request_detail_with_decision_identity(self):
        self.employee.roles.first().permissions.add(
            get_permission_by_code("demande_absence.update")
        )
        demande = self.create_demande(self.other_employee)
        demande.statut = "REFUSEE"
        demande.valideur = self.employee
        demande.date_validation = timezone.now()
        demande.save(update_fields=["statut", "valideur", "date_validation"])

        response = self.client.get(reverse("demande-absence-detail", args=[demande.pk]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["employe"], self.other_employee.pk)
        self.assertEqual(response.data["statut"], "REFUSEE")
        self.assertEqual(response.data["valideur_nom"], self.employee.nom)
        self.assertEqual(response.data["valideur_prenom"], self.employee.prenom)
        self.assertIsNotNone(response.data["date_validation"])

    def test_request_detail_loads_related_people_in_one_query(self):
        from core.repositories.demande_absence_repository import DemandeAbsenceRepository
        from core.serializers.demande_absence_serializer import DemandeAbsenceDetailSerializer

        demande = self.create_demande(self.employee)
        demande.valideur = self.other_employee
        demande.save(update_fields=["valideur"])

        with self.assertNumQueries(1):
            detail = DemandeAbsenceRepository().get(demande.pk)
            serialized = DemandeAbsenceDetailSerializer(detail).data

        self.assertEqual(serialized["valideur_nom"], self.other_employee.nom)

    def test_calendar_access_combines_permissions_from_multiple_roles(self):
        decision_role = Role.objects.create(nom="ADDITIONAL_PLANNING_MANAGER")
        decision_role.permissions.add(get_permission_by_code("demande_absence.update"))
        self.employee.roles.add(decision_role)
        demande = self.create_demande(self.other_employee)
        demande.statut = "VALIDEE"
        demande.save(update_fields=["statut"])

        response = self.client.get(reverse("planning-events"), {
            "date_debut": "2025-05-01", "date_fin": "2025-05-02",
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(
            event["employe_id"] == self.other_employee.pk
            and event["type_evenement"] == "ABSENCE"
            for event in response.data
        ))
        event_ids = [event["id"] for event in response.data]
        self.assertEqual(len(event_ids), len(set(event_ids)))

    def test_complete_leave_workflow_with_jwt_and_common_quota(self):
        self.leave_type.jours_par_annee = 10
        self.leave_type.save(update_fields=["jours_par_annee"])
        self.employee.roles.first().permissions.add(get_permission_by_code("solde_conge.read"))
        manager_role = Role.objects.create(nom="WORKFLOW_MANAGER")
        manager_role.permissions.add(*[
            get_permission_by_code(code) for code in (
                "demande_absence.read", "demande_absence.update",
                "demande_absence.delete", "solde_conge.read",
            )
        ])
        manager = self.create_employee("WORKFLOW-MANAGER", "workflow@example.com", "WORKFLOW-SSN", role=manager_role)

        def sign_in(employee):
            self.client.force_authenticate(user=None)
            self.client.credentials()
            response = self.client.post(reverse("auth-login"), {
                "email": employee.email, "password": "SecurePassword123!",
            }, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

        def submit_request(start, end):
            response = self.client.post(self.url, {
                "type_conge": self.leave_type.pk, "date_debut": start,
                "date_fin": end, "motif": "Parcours de test isolé",
            }, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
            return response.data["id"]

        def check_balance(taken, pending):
            response = self.client.get(reverse("solde-conge-list"), {"annee": 2027})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            balance = next(row for row in response.data if row["employe"] == self.employee.pk and row["type_conge"] == self.leave_type.pk)
            self.assertEqual((balance["acquis"], balance["pris"], balance["en_attente"], balance["disponible"]),
                             (10, taken, pending, 10 - taken - pending))

        sign_in(self.employee)
        check_balance(0, 0)
        first = submit_request("2027-01-04", "2027-01-05")
        check_balance(0, 2)
        forbidden = self.client.post(reverse("demande-absence-valider", args=[first]))
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)
        sign_in(manager)
        approved = self.client.post(reverse("demande-absence-valider", args=[first]))
        self.assertEqual(approved.status_code, status.HTTP_200_OK)
        check_balance(2, 0)
        planning = self.client.get(reverse("planning-events"), {"date_debut": "2027-01-04", "date_fin": "2027-01-05"})
        self.assertEqual(planning.status_code, status.HTTP_200_OK)
        employee_events = [event for event in planning.data if event["employe_id"] == self.employee.pk]
        self.assertTrue(employee_events)
        self.assertTrue(all(event["type_evenement"] == "ABSENCE" for event in employee_events))
        sign_in(self.employee)
        second = submit_request("2027-01-06", "2027-01-06")
        check_balance(2, 1)
        sign_in(manager)
        rejected = self.client.post(reverse("demande-absence-refuser", args=[second]))
        self.assertEqual(rejected.status_code, status.HTTP_200_OK)
        check_balance(2, 0)
        sign_in(self.employee)
        third = submit_request("2027-01-07", "2027-01-07")
        sign_in(manager)
        deleted = self.client.delete(reverse("demande-absence-detail", args=[third]))
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.client.get(reverse("demande-absence-detail", args=[third])).status_code, status.HTTP_404_NOT_FOUND)
        check_balance(2, 0)

    def test_employee_creates_request_for_self_and_cannot_set_status(self):
        response = self.client.post(
            self.url,
            {
                "type_conge": self.leave_type.pk,
                "date_debut": "2025-05-01",
                "date_fin": "2025-05-02",
                "motif": "Repos",
                "employe": self.other_employee.pk,
                "statut": "VALIDEE",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        demande = DemandeAbsence.objects.get(pk=response.data["id"])
        self.assertEqual(demande.employe, self.employee)
        self.assertEqual(demande.statut, "EN_ATTENTE")
        balance = SoldeConge.objects.get(
            employe=self.employee,
            type_conge=self.leave_type,
            annee=2025,
        )
        self.assertEqual(balance.acquis, self.leave_type.jours_par_annee)

    def test_employee_cannot_request_more_weekdays_than_annual_quota(self):
        self.leave_type.jours_par_annee = 2
        self.leave_type.save(update_fields=["jours_par_annee"])

        response = self.client.post(
            self.url,
            {
                "type_conge": self.leave_type.pk,
                "date_debut": "2025-05-05",
                "date_fin": "2025-05-07",
                "motif": "Repos",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("quota", str(response.data).lower())
        self.assertFalse(DemandeAbsence.objects.filter(employe=self.employee).exists())
        self.assertFalse(SoldeConge.objects.filter(employe=self.employee).exists())

    def test_pending_requests_reserve_quota_and_show_available_days(self):
        from core.services.solde_conge_service import solde_conge_service

        self.leave_type.jours_par_annee = 2
        self.leave_type.save(update_fields=["jours_par_annee"])
        first = self.client.post(
            self.url,
            {
                "type_conge": self.leave_type.pk,
                "date_debut": "2025-05-05",
                "date_fin": "2025-05-06",
                "motif": "Première demande",
            },
            format="json",
        )
        second = self.client.post(
            self.url,
            {
                "type_conge": self.leave_type.pk,
                "date_debut": "2025-05-07",
                "date_fin": "2025-05-08",
                "motif": "Deuxième demande",
            },
            format="json",
        )

        self.assertEqual(first.status_code, status.HTTP_201_CREATED, first.data)
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)
        balance = solde_conge_service.get_balances(2025, self.employee.pk)[0]
        self.assertEqual(balance["pris"], 0)
        self.assertEqual(balance["en_attente"], 2)
        self.assertEqual(balance["disponible"], 0)

    def test_employee_lists_only_own_requests(self):
        own_request = self.create_demande(self.employee)
        self.create_demande(self.other_employee)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [own_request.pk])

    def test_calendar_returns_overlapping_approved_absences_without_exposing_motif(self):
        own_request = self.create_demande(self.employee)
        own_request.statut = "VALIDEE"
        own_request.save(update_fields=["statut"])
        other_request = self.create_demande(self.other_employee)
        other_request.statut = "VALIDEE"
        other_request.save(update_fields=["statut"])
        self.create_demande(self.employee)

        response = self.client.get(
            reverse("planning-events"),
            {
                "date_debut": "2025-05-02",
                "date_fin": "2025-05-05",
                "employe": self.other_employee.pk,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(
            [item["demande_absence_id"] for item in response.data if item["type_evenement"] == "ABSENCE"],
            [own_request.pk],
        )
        self.assertEqual(
            [item["date_debut"] for item in response.data if item["type_evenement"] == "PRESENCE_PREVUE"],
            ["2025-05-05"],
        )
        self.assertNotIn("motif", response.data[0])

    def test_calendar_manager_can_filter_by_department(self):
        department = Departement.objects.create(nom="RH", code="RH")
        other_department = Departement.objects.create(nom="Finance", code="FIN")
        self.employee.department = department
        self.employee.save(update_fields=["department"])
        self.other_employee.department = other_department
        self.other_employee.save(update_fields=["department"])
        own_request = self.create_demande(self.employee)
        own_request.statut = "VALIDEE"
        own_request.save(update_fields=["statut"])
        inactive_employee = self.create_employee(
            "CALENDAR-INACTIVE",
            "calendar-inactive@example.com",
            "ABS-SSN-CALENDAR-INACTIVE",
        )
        inactive_employee.department = other_department
        inactive_employee.is_active = False
        inactive_employee.save(update_fields=["department", "is_active"])
        other_request = self.create_demande(self.other_employee)
        other_request.statut = "VALIDEE"
        other_request.save(update_fields=["statut"])
        manager_role = Role.objects.create(nom="ABSENCE_CALENDAR_MANAGER")
        manager_role.permissions.add(
            get_permission_by_code("demande_absence.read"),
            get_permission_by_code("demande_absence.update"),
        )
        manager = self.create_employee(
            "CALENDAR-MANAGER",
            "calendar-manager@example.com",
            "ABS-SSN-CALENDAR-MANAGER",
            role=manager_role,
        )
        self.client.force_authenticate(user=manager)

        response = self.client.get(
            reverse("planning-events"),
            {
                "date_debut": "2025-05-01",
                "date_fin": "2025-05-31",
                "departement": other_department.pk,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertTrue(response.data)
        self.assertTrue(
            all(item["employe_id"] == self.other_employee.pk for item in response.data)
        )
        self.assertIn("ABSENCE", {item["type_evenement"] for item in response.data})
        self.assertIn(
            "PRESENCE_PREVUE",
            {item["type_evenement"] for item in response.data},
        )
        self.assertIn(
            other_request.pk,
            [
                item["demande_absence_id"]
                for item in response.data
                if item["type_evenement"] == "ABSENCE"
            ],
        )

    def test_employee_cannot_read_another_employees_request(self):
        other_request = self.create_demande(self.other_employee)

        response = self.client.get(
            reverse("demande-absence-detail", args=[other_request.pk])
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_employee_can_read_own_request(self):
        own_request = self.create_demande(self.employee)

        response = self.client.get(
            reverse("demande-absence-detail", args=[own_request.pk])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], own_request.pk)

    def test_invalid_date_range_is_rejected(self):
        response = self.client.post(
            self.url,
            {
                "type_conge": self.leave_type.pk,
                "date_debut": "2025-05-03",
                "date_fin": "2025-05-02",
                "motif": "Repos",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("date_fin", response.data)

    def test_authorized_manager_can_approve_and_is_recorded(self):
        demande = self.create_demande(self.employee)
        manager_role = Role.objects.create(nom="ABSENCE_APPROVER")
        manager_role.permissions.add(
            get_permission_by_code("demande_absence.update")
        )
        manager = self.create_employee(
            "MANAGER-001",
            "manager@example.com",
            "ABS-SSN-MANAGER",
            role=manager_role,
        )
        self.client.force_authenticate(user=manager)

        response = self.client.post(
            reverse("demande-absence-valider", args=[demande.pk]),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        demande.refresh_from_db()
        self.assertEqual(demande.statut, "VALIDEE")
        self.assertEqual(demande.valideur, manager)
        self.assertIsNotNone(demande.date_validation)

    def test_approval_persists_total_from_all_approved_dates_without_double_counting(self):
        balance = SoldeConge.objects.create(
            employe=self.employee,
            type_conge=self.leave_type,
            annee=2025,
            acquis=25,
            pris=0,
        )
        DemandeAbsence.objects.create(
            employe=self.employee,
            type_conge=self.leave_type,
            date_debut=date(2025, 5, 5),
            date_fin=date(2025, 5, 6),
            motif="Ancienne demande",
            statut="VALIDEE",
        )
        pending_request = DemandeAbsence.objects.create(
            employe=self.employee,
            type_conge=self.leave_type,
            date_debut=date(2025, 5, 7),
            date_fin=date(2025, 5, 9),
            motif="Demande récente",
        )
        manager_role = Role.objects.create(nom="ABSENCE_APPROVER_RECALC")
        manager_role.permissions.add(
            get_permission_by_code("demande_absence.update")
        )
        manager = self.create_employee(
            "MANAGER-RECALC",
            "manager-recalc@example.com",
            "ABS-SSN-MANAGER-RECALC",
            role=manager_role,
        )
        self.client.force_authenticate(user=manager)

        response = self.client.post(
            reverse("demande-absence-valider", args=[pending_request.pk]),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        balance.refresh_from_db()
        self.assertEqual(balance.pris, 5)

    def test_manager_cannot_approve_request_that_exceeds_annual_quota(self):
        self.leave_type.jours_par_annee = 2
        self.leave_type.save(update_fields=["jours_par_annee"])
        pending_request = DemandeAbsence.objects.create(
            employe=self.employee,
            type_conge=self.leave_type,
            date_debut=date(2025, 5, 5),
            date_fin=date(2025, 5, 7),
            motif="Dépassement quota",
        )
        manager_role = Role.objects.create(nom="ABSENCE_QUOTA_APPROVER")
        manager_role.permissions.add(get_permission_by_code("demande_absence.update"))
        manager = self.create_employee(
            "MANAGER-QUOTA",
            "manager-quota@example.com",
            "ABS-SSN-MANAGER-QUOTA",
            role=manager_role,
        )
        self.client.force_authenticate(user=manager)

        response = self.client.post(
            reverse("demande-absence-valider", args=[pending_request.pk]),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("quota", str(response.data).lower())
        pending_request.refresh_from_db()
        self.assertEqual(pending_request.statut, "EN_ATTENTE")
        self.assertFalse(SoldeConge.objects.filter(employe=self.employee).exists())

    def test_approval_rejects_overlapping_approved_absence_for_same_employee(self):
        approved = DemandeAbsence.objects.create(
            employe=self.employee,
            type_conge=self.leave_type,
            date_debut=date(2025, 5, 5),
            date_fin=date(2025, 5, 7),
            motif="Congé payé",
            statut="VALIDEE",
        )
        pending = DemandeAbsence.objects.create(
            employe=self.employee,
            type_conge=self.leave_type,
            date_debut=date(2025, 5, 7),
            date_fin=date(2025, 5, 9),
            motif="Absence à valider",
        )
        manager_role = Role.objects.create(nom="ABSENCE_OVERLAP_APPROVER")
        manager_role.permissions.add(get_permission_by_code("demande_absence.update"))
        manager = self.create_employee(
            "MANAGER-OVERLAP",
            "manager-overlap@example.com",
            "ABS-SSN-MANAGER-OVERLAP",
            role=manager_role,
        )
        self.client.force_authenticate(user=manager)

        response = self.client.post(
            reverse("demande-absence-valider", args=[pending.pk]),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(str(approved.pk), str(response.data["date_debut"]))
        pending.refresh_from_db()
        self.assertEqual(pending.statut, "EN_ATTENTE")

    def test_approval_allows_date_overlap_when_only_weekend_days_overlap(self):
        DemandeAbsence.objects.create(
            employe=self.employee,
            type_conge=self.leave_type,
            date_debut=date(2025, 5, 3),
            date_fin=date(2025, 5, 4),
            motif="Week-end",
            statut="VALIDEE",
        )
        pending = DemandeAbsence.objects.create(
            employe=self.employee,
            type_conge=self.leave_type,
            date_debut=date(2025, 5, 4),
            date_fin=date(2025, 5, 5),
            motif="Lundi",
        )
        manager_role = Role.objects.create(nom="ABSENCE_WEEKEND_APPROVER")
        manager_role.permissions.add(get_permission_by_code("demande_absence.update"))
        manager = self.create_employee(
            "MANAGER-WEEKEND",
            "manager-weekend@example.com",
            "ABS-SSN-MANAGER-WEEKEND",
            role=manager_role,
        )
        self.client.force_authenticate(user=manager)

        response = self.client.post(
            reverse("demande-absence-valider", args=[pending.pk]),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        pending.refresh_from_db()
        self.assertEqual(pending.statut, "VALIDEE")

    def test_authorized_manager_can_reject_request(self):
        demande = self.create_demande(self.employee)
        manager_role = Role.objects.create(nom="ABSENCE_REJECTOR")
        manager_role.permissions.add(
            get_permission_by_code("demande_absence.update")
        )
        manager = self.create_employee(
            "MANAGER-002",
            "manager2@example.com",
            "ABS-SSN-MANAGER-2",
            role=manager_role,
        )
        self.client.force_authenticate(user=manager)

        response = self.client.post(
            reverse("demande-absence-refuser", args=[demande.pk]),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        demande.refresh_from_db()
        self.assertEqual(demande.statut, "REFUSEE")
        self.assertEqual(demande.valideur, manager)

    def test_employee_without_decision_permission_cannot_approve(self):
        demande = self.create_demande(self.employee)

        response = self.client.post(
            reverse("demande-absence-valider", args=[demande.pk]),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SoldeCongeTests(APITestCase):
    def setUp(self):
        self.employee = self.create_employee(
            "BALANCE-001",
            "balance@example.com",
            "BALANCE-SSN-001",
        )
        self.other_employee = self.create_employee(
            "BALANCE-002",
            "balance-other@example.com",
            "BALANCE-SSN-002",
        )
        self.leave_type = TypeConge.objects.create(
            code="CP",
            libelle="Congé payé",
            jours_par_annee=25,
        )
        self.sick_type = TypeConge.objects.create(
            code="MALADIE",
            libelle="Maladie",
        )
        read_role = Role.objects.create(nom="SOLDE_READER")
        read_role.permissions.add(get_permission_by_code("solde_conge.read"))
        self.employee.roles.add(read_role)
        self.client.force_authenticate(user=self.employee)
        self.url = reverse("solde-conge-list")

    def create_employee(self, matricule, email, social_security_number):
        return Employe.objects.create_user(
            email=email,
            password="SecurePassword123!",
            matricule=matricule,
            nom="Test",
            prenom="Employe",
            date_naissance=date(1990, 1, 1),
            adresse="1 rue de Test",
            telephone="0600000000",
            num_secu_sociale=social_security_number,
            date_entree=date(2020, 1, 1),
        )

    def create_absence(self, employee, start, end, leave_type, status_value):
        return DemandeAbsence.objects.create(
            employe=employee,
            type_conge=leave_type,
            date_debut=date.fromisoformat(start),
            date_fin=date.fromisoformat(end),
            motif="Test solde",
            statut=status_value,
        )

    def test_reader_cannot_update_acquired_days(self):
        balance = SoldeConge.objects.create(
            employe=self.employee, type_conge=self.leave_type, annee=2026, acquis=25
        )
        response = self.client.put(
            reverse("solde-conge-detail", args=[balance.pk]), {"acquis": 30}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        balance.refresh_from_db()
        self.assertEqual(balance.acquis, 25)

    def test_even_manager_cannot_override_individual_quota(self):
        self.employee.roles.first().permissions.add(get_permission_by_code("solde_conge.update"))
        balance = SoldeConge.objects.create(employe=self.employee, type_conge=self.leave_type, annee=2026, acquis=25)
        response = self.client.put(reverse("solde-conge-detail", args=[balance.pk]), {"acquis": 99}, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        balance.refresh_from_db()
        self.assertEqual(balance.acquis, 25)

    def test_balances_are_visible_without_manual_allocation(self):
        response = self.client.get(self.url, {"annee": 2026})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        balance = next(item for item in response.data if item["type_conge"] == self.leave_type.pk)
        self.assertEqual(balance["acquis"], self.leave_type.jours_par_annee)
        self.assertEqual(balance["disponible"], self.leave_type.jours_par_annee)
        self.assertEqual({item["employe"] for item in response.data}, {self.employee.pk})
        self.assertFalse(SoldeConge.objects.exists())

    def test_legacy_individual_quota_is_ignored(self):
        SoldeConge.objects.create(employe=self.employee, type_conge=self.leave_type, annee=2026, acquis=99)
        response = self.client.get(self.url, {"annee": 2026})
        balance = next(item for item in response.data if item["type_conge"] == self.leave_type.pk)
        self.assertEqual(balance["acquis"], 25)

    def test_type_update_can_keep_existing_code(self):
        self.employee.roles.first().permissions.add(get_permission_by_code("conge.update"))
        response = self.client.put(reverse("conge-type-detail", args=[self.leave_type.pk]), {
            "code": self.leave_type.code, "libelle": "Congé annuel", "jours_par_annee": 30,
            "est_payant": True, "actif": True,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.leave_type.refresh_from_db()
        self.assertEqual(self.leave_type.jours_par_annee, 30)

    def test_type_codes_are_generated_and_cannot_be_changed_by_client(self):
        self.employee.roles.first().permissions.add(
            get_permission_by_code("conge.create"), get_permission_by_code("conge.update")
        )
        payload = {"libelle": "Congé familial", "jours_par_annee": 8, "code": "MANUAL"}
        first = self.client.post(reverse("conge-type-list"), payload, format="json")
        second = self.client.post(reverse("conge-type-list"), payload, format="json")
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(first.data["code"], "MANUAL")
        self.assertNotEqual(first.data["code"], second.data["code"])
        changed = self.client.put(reverse("conge-type-detail", args=[first.data["id"]]),
                                  {**payload, "code": "OVERRIDE"}, format="json")
        self.assertEqual(changed.status_code, status.HTTP_200_OK)
        self.assertEqual(changed.data["code"], first.data["code"])

    def test_legacy_higher_quota_does_not_authorize_excessive_request(self):
        self.employee.roles.first().permissions.add(get_permission_by_code("demande_absence.create"))
        SoldeConge.objects.create(employe=self.employee, type_conge=self.leave_type, annee=2026, acquis=99)
        response = self.client.post(reverse("demande-absence-list"), {
            "type_conge": self.leave_type.pk, "date_debut": "2026-01-01",
            "date_fin": "2026-02-28", "motif": "Quota commun",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("quota", str(response.data).lower())
        self.assertFalse(DemandeAbsence.objects.filter(employe=self.employee).exists())

    def test_manager_can_create_and_delete_unused_leave_type(self):
        self.employee.roles.first().permissions.add(
            get_permission_by_code("conge.create"), get_permission_by_code("conge.delete")
        )
        created = self.client.post(reverse("conge-type-list"), {
            "code": "FAMILY", "libelle": "Congé familial", "jours_par_annee": 8,
            "est_payant": True, "actif": True,
        }, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        deleted = self.client.delete(reverse("conge-type-detail", args=[created.data["id"]]))
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(TypeConge.objects.filter(code="FAMILY").exists())

    def test_reader_cannot_manage_leave_types(self):
        created = self.client.post(reverse("conge-type-list"), {
            "code": "DENIED", "libelle": "Interdit", "jours_par_annee": 8,
        }, format="json")
        deleted = self.client.delete(reverse("conge-type-detail", args=[self.leave_type.pk]))
        self.assertEqual(created.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(deleted.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(TypeConge.objects.filter(pk=self.leave_type.pk).exists())

    def test_type_quota_change_applies_to_all_existing_balances(self):
        from core.services.conge_service import conge_service
        first = SoldeConge.objects.create(employe=self.employee, type_conge=self.leave_type, annee=2026, acquis=25, pris=4)
        second = SoldeConge.objects.create(employe=self.other_employee, type_conge=self.leave_type, annee=2026, acquis=99)
        conge_service.update_type(self.leave_type.pk, {"jours_par_annee": 30, "code": "FORCED"})
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual((first.acquis, second.acquis, first.pris), (30, 30, 4))
        self.leave_type.refresh_from_db()
        self.assertEqual(self.leave_type.code, "CP")

    def test_type_with_balance_cannot_be_deleted(self):
        self.employee.roles.first().permissions.add(get_permission_by_code("conge.delete"))
        balance = SoldeConge.objects.create(
            employe=self.employee, type_conge=self.leave_type, annee=2026, acquis=25
        )
        response = self.client.delete(reverse("conge-type-detail", args=[self.leave_type.pk]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(SoldeConge.objects.filter(pk=balance.pk).exists())
        self.assertTrue(TypeConge.objects.filter(pk=self.leave_type.pk).exists())

    def test_type_with_request_cannot_be_deleted(self):
        self.employee.roles.first().permissions.add(get_permission_by_code("conge.delete"))
        self.create_absence(self.employee, "2026-01-01", "2026-01-02", self.leave_type, "EN_ATTENTE")
        response = self.client.delete(reverse("conge-type-detail", args=[self.leave_type.pk]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(TypeConge.objects.filter(pk=self.leave_type.pk).exists())

    def test_balance_counts_approved_unique_weekdays_for_employee_and_type(self):
        balance = SoldeConge.objects.create(
            employe=self.employee,
            type_conge=self.leave_type,
            annee=2026,
            acquis=25,
        )
        SoldeConge.objects.create(
            employe=self.other_employee,
            type_conge=self.leave_type,
            annee=2026,
            acquis=20,
        )
        self.create_absence(
            self.employee,
            "2026-11-06",
            "2026-11-10",
            self.leave_type,
            "VALIDEE",
        )
        self.create_absence(
            self.employee,
            "2026-11-10",
            "2026-11-11",
            self.leave_type,
            "VALIDEE",
        )
        self.create_absence(
            self.employee,
            "2026-11-12",
            "2026-11-13",
            self.leave_type,
            "EN_ATTENTE",
        )
        self.create_absence(
            self.employee,
            "2026-11-12",
            "2026-11-13",
            self.sick_type,
            "VALIDEE",
        )

        response = self.client.get(self.url, {"annee": 2026})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual({item["employe"] for item in response.data}, {self.employee.pk})
        self.assertEqual(response.data[0]["id"], balance.pk)
        self.assertEqual(response.data[0]["pris"], 4)
        self.assertEqual(response.data[0]["restant"], 21)
        self.assertEqual(response.data[0]["en_attente"], 2)
        self.assertEqual(response.data[0]["disponible"], 19)

    def test_balance_counts_only_workdays_inside_requested_year(self):
        SoldeConge.objects.create(
            employe=self.employee,
            type_conge=self.leave_type,
            annee=2027,
            acquis=25,
        )
        self.create_absence(
            self.employee,
            "2026-12-31",
            "2027-01-04",
            self.leave_type,
            "VALIDEE",
        )

        response = self.client.get(self.url, {"annee": 2027})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["pris"], 2)
        self.assertEqual(response.data[0]["restant"], 23)

    def test_employee_cannot_create_balance_without_create_permission(self):
        response = self.client.post(
            self.url,
            {
                "employe": self.employee.pk,
                "type_conge": self.leave_type.pk,
                "annee": 2026,
                "acquis": 25,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_even_manager_cannot_create_individual_quota(self):
        self.employee.roles.first().permissions.add(get_permission_by_code("solde_conge.create"))
        response = self.client.post(self.url, {"employe": self.employee.pk, "type_conge": self.leave_type.pk, "annee": 2026, "acquis": 99}, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertFalse(SoldeConge.objects.exists())

    def test_invalid_year_is_rejected(self):
        response = self.client.get(self.url, {"annee": "abc"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("annee", response.data)


class CoordonneesBancairesAccessTests(APITestCase):
    def setUp(self):
        self.owner = self.create_employee(
            "BANK-OWNER-001",
            "bank-owner@example.com",
            "BANK-SSN-001",
        )
        self.other_employee = self.create_employee(
            "BANK-OTHER-001",
            "bank-other@example.com",
            "BANK-SSN-002",
        )
        owner_role = Role.objects.create(nom="BANK_OWNER")
        owner_role.permissions.add(
            get_permission_by_code("coordonnees_bancaires.read"),
            get_permission_by_code("coordonnees_bancaires.create"),
            get_permission_by_code("coordonnees_bancaires.update"),
        )
        self.owner.roles.add(owner_role)
        self.client.force_authenticate(user=self.owner)
        self.url = reverse("coordonnees-bancaires-list")

    def create_employee(self, matricule, email, social_security_number, role=None):
        employee = Employe.objects.create_user(
            email=email,
            password="SecurePassword123!",
            matricule=matricule,
            nom="Test",
            prenom="Employe",
            date_naissance=date(1990, 1, 1),
            adresse="1 rue de Test",
            telephone="0600000000",
            num_secu_sociale=social_security_number,
            date_entree=date(2020, 1, 1),
        )
        if role:
            employee.roles.add(role)
        return employee

    def create_bank_details(self, employee, iban):
        return CoordonneesBancaires.objects.create(
            employe=employee,
            iban=iban,
            bic="TESTFRPP",
            swift="TESTFRPPXXX",
            banque="Banque de test",
        )

    def test_employee_list_is_limited_to_own_bank_details(self):
        own_details = self.create_bank_details(self.owner, "TEST-IBAN-OWNER-001")
        self.create_bank_details(self.other_employee, "TEST-IBAN-OTHER-001")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [own_details.pk])

    def test_employee_cannot_read_another_employees_bank_details(self):
        other_details = self.create_bank_details(
            self.other_employee,
            "TEST-IBAN-OTHER-002",
        )

        response = self.client.get(
            reverse("coordonnees-bancaires-detail", args=[other_details.pk])
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_employee_cannot_assign_or_reassign_bank_details_to_another_employee(self):
        response = self.client.post(
            self.url,
            {
                "iban": "TEST-IBAN-OWNER-002",
                "bic": "TESTFRPP",
                "swift": "TESTFRPPXXX",
                "banque": "Banque de test",
                "employe": self.other_employee.pk,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        created = CoordonneesBancaires.objects.get(pk=response.data["id"])
        self.assertEqual(created.employe, self.owner)

        other_details = self.create_bank_details(
            self.other_employee,
            "TEST-IBAN-OTHER-003",
        )
        response = self.client.put(
            reverse("coordonnees-bancaires-detail", args=[created.pk]),
            {
                "iban": "TEST-IBAN-OWNER-002",
                "bic": "TESTFRPP",
                "swift": "TESTFRPPXXX",
                "banque": "Banque de test modifiée",
                "employe": self.other_employee.pk,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        created.refresh_from_db()
        self.assertEqual(created.employe, self.owner)
        self.assertNotEqual(created.employe, other_details.employe)

    def test_update_permission_can_list_all_bank_details(self):
        self.create_bank_details(self.owner, "TEST-IBAN-OWNER-004")
        self.create_bank_details(self.other_employee, "TEST-IBAN-OTHER-004")
        manager_role = Role.objects.create(nom="BANK_MANAGER")
        manager_role.permissions.add(
            get_permission_by_code("coordonnees_bancaires.read"),
            get_permission_by_code("coordonnees_bancaires.manage"),
        )
        manager = self.create_employee(
            "BANK-MANAGER-001",
            "bank-manager@example.com",
            "BANK-SSN-MANAGER-001",
            manager_role,
        )
        self.client.force_authenticate(user=manager)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)


class DomainCrudTests(APITestCase):
    def setUp(self):
        self.department = Departement.objects.create(
            nom="Administration",
            code="ADM",
        )
        admin_role = Role.objects.create(nom="ADMIN_RH")
        admin_role.permissions.set(
            AuthPermission.objects.filter(content_type__app_label="core")
        )
        self.admin_employee = self.create_employee(
            "ADMIN-001",
            "admin-domain@example.com",
            "000000001",
            admin_role,
        )
        self.employee = self.create_employee(
            "EMP-100",
            "domain-employee@example.com",
            "000000100",
        )
        self.client.force_authenticate(user=self.admin_employee)

        self.leave_type = TypeConge.objects.create(
            code="DOMAIN-CP",
            libelle="Congé payé",
            jours_par_annee=25,
        )
        self.contract_type = TypeContrat.objects.create(type="CDI")
        self.other_contract_type = TypeContrat.objects.create(type="CDD")
        self.document_type = TypeDocument.objects.create(
            code="IDENTITE",
            libelle="Pièce d'identité",
        )
        self.contract = Contrat.objects.create(
            date_debut=date(2024, 1, 1),
            salaire_base="2500.00",
            employe=self.employee,
        )
        self.document = Document.objects.create(
            type_document=self.document_type,
            fichier="contrat-initial.pdf",
            date_depot=date(2024, 1, 2),
        )
        self.transfer = OrdreVirement.objects.create(
            periode="2024-01",
            date_generation=timezone.now(),
            employe=self.employee,
        )

    def create_employee(self, matricule, email, social_security_number, role=None):
        employee = Employe.objects.create_user(
            email=email,
            password="SecurePassword123!",
            matricule=matricule,
            nom="Test",
            prenom="Employe",
            date_naissance=date(1990, 1, 1),
            adresse="1 rue de Test",
            telephone="0600000000",
            num_secu_sociale=social_security_number,
            date_entree=date(2020, 1, 1),
            department=self.department,
        )
        if role:
            employee.roles.add(role)
        return employee

    def test_contract_api_requires_daily_schedule_hours(self):
        missing_hours = self.client.post(
            reverse("contrat-list"),
            {
                "date_debut": "2026-10-01",
                "date_fin": None,
                "salaire_base": "3000.00",
                "employe": self.employee.pk,
            },
            format="json",
        )
        self.assertEqual(missing_hours.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("heures_journalieres", missing_hours.data)

        update_url = reverse("contrat-detail", args=[self.contract.pk])
        valid_hours = self.client.put(
            update_url,
            {
                "date_debut": "2024-01-01",
                "date_fin": None,
                "salaire_base": "2500.00",
                "heures_journalieres": "8.00",
                "statut": "EN_COURS",
                "employe": self.employee.pk,
                "type": [],
            },
            format="json",
        )
        self.assertEqual(valid_hours.status_code, status.HTTP_200_OK, valid_hours.data)
        self.assertEqual(valid_hours.data["heures_journalieres"], "8.00")

        excessive_hours = self.client.put(
            update_url,
            {
                "date_debut": "2024-01-01",
                "date_fin": None,
                "salaire_base": "2500.00",
                "heures_journalieres": "24.01",
                "statut": "EN_COURS",
                "employe": self.employee.pk,
                "type": [],
            },
            format="json",
        )
        self.assertEqual(
            excessive_hours.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn("heures_journalieres", excessive_hours.data)

    def test_timesheet_model_validates_week_dates_and_task_project(self):
        project = Projet.objects.create(
            code="TIMESHEET-PROJ-1",
            nom="Projet test feuille",
        )
        other_project = Projet.objects.create(
            code="TIMESHEET-PROJ-2",
            nom="Autre projet feuille",
        )
        task = TacheProjet.objects.create(
            projet=project,
            code="TASK-1",
            nom="Tâche test",
        )
        sheet = FeuilleTemps.objects.create(
            employe=self.employee,
            semaine_debut=date(2026, 10, 19),
        )
        valid_line = LigneFeuilleTemps(
            feuille=sheet,
            date_travail=date(2026, 10, 25),
            projet=project,
            tache=task,
            heures=Decimal("8.00"),
        )
        valid_line.full_clean()

        duplicate_week = FeuilleTemps(
            employe=self.employee,
            semaine_debut=date(2026, 10, 19),
        )
        with self.assertRaises(DjangoValidationError):
            duplicate_week.full_clean()

        invalid_week = FeuilleTemps(
            employe=self.employee,
            semaine_debut=date(2026, 10, 20),
        )
        with self.assertRaises(DjangoValidationError):
            invalid_week.full_clean()

        outside_week = LigneFeuilleTemps(
            feuille=sheet,
            date_travail=date(2026, 10, 26),
            projet=project,
            tache=task,
            heures=Decimal("1.00"),
        )
        with self.assertRaises(DjangoValidationError):
            outside_week.full_clean()

        mismatched_task = LigneFeuilleTemps(
            feuille=sheet,
            date_travail=date(2026, 10, 20),
            projet=other_project,
            tache=task,
            heures=Decimal("1.00"),
        )
        with self.assertRaises(DjangoValidationError):
            mismatched_task.full_clean()

        excessive_line_hours = LigneFeuilleTemps(
            feuille=sheet,
            date_travail=date(2026, 10, 20),
            projet=project,
            tache=task,
            heures=Decimal("24.01"),
        )
        with self.assertRaises(DjangoValidationError):
            excessive_line_hours.full_clean()

    def create_timesheet_project(self, project_code="TIMESHEET-API-PROJ"):
        project = Projet.objects.create(
            code=project_code,
            nom=f"Projet {project_code}",
        )
        task = TacheProjet.objects.create(
            projet=project,
            code="TASK-API",
            nom="Tâche API",
        )
        AffectationProjet.objects.create(
            projet=project,
            employe=self.admin_employee,
        )
        Contrat.objects.create(
            date_debut=date(2024, 1, 1),
            salaire_base=Decimal("2500.00"),
            heures_journalieres=Decimal("8.00"),
            employe=self.admin_employee,
        )
        return project, task

    def create_submitted_timesheet(self, project_code="TIMESHEET-REVIEW-PROJ"):
        project, task = self.create_timesheet_project(project_code)
        sheet = FeuilleTemps.objects.create(
            employe=self.admin_employee,
            semaine_debut=date(2026, 10, 19),
            statut="SOUMISE",
        )
        LigneFeuilleTemps.objects.create(
            feuille=sheet,
            date_travail=date(2026, 10, 20),
            projet=project,
            tache=task,
            heures=Decimal("2.00"),
        )
        return sheet

    def test_timesheet_api_creates_lists_filters_and_submits_week(self):
        project, task = self.create_timesheet_project()
        payload = {
            "semaine_debut": "2026-10-19",
            "lignes": [
                {
                    "date_travail": "2026-10-20",
                    "projet": project.pk,
                    "tache": task.pk,
                    "heures": "4.00",
                    "commentaire": "Analyse",
                },
                {
                    "date_travail": "2026-10-20",
                    "projet": project.pk,
                    "tache": task.pk,
                    "heures": "4.00",
                    "commentaire": "Réunion",
                },
            ],
        }

        created = self.client.post(
            reverse("feuille-temps-list"),
            payload,
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED, created.data)
        sheet_id = created.data["id"]
        self.assertEqual(created.data["statut"], "BROUILLON")
        self.assertEqual(len(created.data["lignes"]), 2)

        by_week = self.client.get(
            reverse("feuille-temps-list"),
            {"semaine_debut": "2026-10-19"},
        )
        self.assertEqual(by_week.status_code, status.HTTP_200_OK)
        self.assertEqual(len(by_week.data), 1)

        by_day = self.client.get(
            reverse("feuille-temps-list"),
            {"date_travail": "2026-10-20"},
        )
        self.assertEqual(by_day.status_code, status.HTTP_200_OK)
        self.assertEqual(len(by_day.data), 1)

        submitted = self.client.post(
            reverse("feuille-temps-soumettre", args=[sheet_id]),
            {},
            format="json",
        )
        self.assertEqual(submitted.status_code, status.HTTP_200_OK, submitted.data)
        self.assertEqual(submitted.data["statut"], "SOUMISE")

        update_after_submit = self.client.put(
            reverse("feuille-temps-detail", args=[sheet_id]),
            payload,
            format="json",
        )
        self.assertEqual(
            update_after_submit.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_timesheet_api_enforces_daily_contract_hours_and_assignment(self):
        project, task = self.create_timesheet_project()
        endpoint = reverse("feuille-temps-list")
        over_limit = self.client.post(
            endpoint,
            {
                "semaine_debut": "2026-10-19",
                "lignes": [
                    {
                        "date_travail": "2026-10-20",
                        "projet": project.pk,
                        "tache": task.pk,
                        "heures": "8.01",
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(over_limit.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("heures", over_limit.data)
        self.assertFalse(
            FeuilleTemps.objects.filter(
                employe=self.admin_employee,
                semaine_debut=date(2026, 10, 19),
            ).exists()
        )

        unassigned_project = Projet.objects.create(
            code="TIMESHEET-UNASSIGNED",
            nom="Projet sans affectation",
        )
        unassigned_task = TacheProjet.objects.create(
            projet=unassigned_project,
            code="TASK-UNASSIGNED",
            nom="Tâche sans affectation",
        )
        unassigned = self.client.post(
            endpoint,
            {
                "semaine_debut": "2026-10-19",
                "lignes": [
                    {
                        "date_travail": "2026-10-20",
                        "projet": unassigned_project.pk,
                        "tache": unassigned_task.pk,
                        "heures": "1.00",
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(unassigned.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("projet", unassigned.data)

    def test_timesheet_api_only_exposes_the_authenticated_employees_sheets(self):
        project, task = self.create_timesheet_project()
        response = self.client.post(
            reverse("feuille-temps-list"),
            {
                "semaine_debut": "2026-10-19",
                "lignes": [
                    {
                        "date_travail": "2026-10-20",
                        "projet": project.pk,
                        "tache": task.pk,
                        "heures": "2.00",
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        other_employee = self.create_employee(
            "OTHER-TIMESHEET-001",
            "other-timesheet@example.com",
            "OTHER-TIMESHEET-SSN",
        )
        self.client.force_authenticate(user=other_employee)
        detail = self.client.get(
            reverse("feuille-temps-detail", args=[response.data["id"]])
        )
        self.assertEqual(detail.status_code, status.HTTP_404_NOT_FOUND)

    def test_timesheet_submission_rechecks_project_and_assignment(self):
        project, task = self.create_timesheet_project()
        created = self.client.post(
            reverse("feuille-temps-list"),
            {
                "semaine_debut": "2026-10-19",
                "lignes": [
                    {
                        "date_travail": "2026-10-20",
                        "projet": project.pk,
                        "tache": task.pk,
                        "heures": "2.00",
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED, created.data)

        project.actif = False
        project.save(update_fields=["actif"])
        submitted = self.client.post(
            reverse("feuille-temps-soumettre", args=[created.data["id"]]),
            {},
            format="json",
        )

        self.assertEqual(submitted.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            FeuilleTemps.objects.get(pk=created.data["id"]).statut,
            "BROUILLON",
        )

    def test_timesheet_review_queue_only_returns_submitted_sheets(self):
        submitted_sheet = self.create_submitted_timesheet()
        FeuilleTemps.objects.create(
            employe=self.admin_employee,
            semaine_debut=date(2026, 10, 12),
            statut="BROUILLON",
        )

        response = self.client.get(reverse("feuille-temps-a-valider"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([sheet["id"] for sheet in response.data], [submitted_sheet.pk])

    def test_timesheet_can_be_approved_only_after_submission(self):
        sheet = self.create_submitted_timesheet()

        response = self.client.post(
            reverse("feuille-temps-valider", args=[sheet.pk]),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["statut"], "VALIDEE")
        self.assertEqual(response.data["valideur"], self.admin_employee.pk)
        self.assertIsNotNone(response.data["date_decision"])
        self.assertEqual(response.data["motif_refus"], "")

        repeated_decision = self.client.post(
            reverse("feuille-temps-valider", args=[sheet.pk]),
            {},
            format="json",
        )
        self.assertEqual(
            repeated_decision.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_refusing_timesheet_requires_and_persists_a_reason(self):
        sheet = self.create_submitted_timesheet()
        endpoint = reverse("feuille-temps-refuser", args=[sheet.pk])

        missing_reason = self.client.post(
            endpoint,
            {"motif": "   "},
            format="json",
        )
        self.assertEqual(missing_reason.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            FeuilleTemps.objects.get(pk=sheet.pk).statut,
            "SOUMISE",
        )

        refusal = self.client.post(
            endpoint,
            {"motif": "  Merci de corriger le détail du mardi.  "},
            format="json",
        )

        self.assertEqual(refusal.status_code, status.HTTP_200_OK, refusal.data)
        self.assertEqual(refusal.data["statut"], "BROUILLON")
        self.assertEqual(
            refusal.data["motif_refus"],
            "Merci de corriger le détail du mardi.",
        )
        self.assertEqual(refusal.data["valideur"], self.admin_employee.pk)

        resubmission = self.client.post(
            reverse("feuille-temps-soumettre", args=[sheet.pk]),
            {},
            format="json",
        )
        self.assertEqual(resubmission.status_code, status.HTTP_200_OK)
        self.assertEqual(resubmission.data["statut"], "SOUMISE")
        self.assertEqual(resubmission.data["motif_refus"], "")
        self.assertIsNone(resubmission.data["valideur"])

    def test_timesheet_review_requires_dedicated_permission(self):
        sheet = self.create_submitted_timesheet()
        reviewer_role = Role.objects.create(nom="TIME_REVIEWER")
        reviewer = self.create_employee(
            "TIME-REVIEWER-001",
            "timesheet-reviewer@example.com",
            "TIME-REVIEWER-SSN",
            reviewer_role,
        )
        self.client.force_authenticate(user=reviewer)

        queue_response = self.client.get(reverse("feuille-temps-a-valider"))
        approval_response = self.client.post(
            reverse("feuille-temps-valider", args=[sheet.pk]),
            {},
            format="json",
        )

        self.assertEqual(queue_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(approval_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_project_costs_use_only_approved_hours_and_monthly_tgm(self):
        project, task = self.create_timesheet_project("TIMESHEET-COST-PROJ")
        approved_sheet = FeuilleTemps.objects.create(
            employe=self.admin_employee,
            semaine_debut=date(2026, 10, 19),
            statut="VALIDEE",
        )
        LigneFeuilleTemps.objects.create(
            feuille=approved_sheet,
            date_travail=date(2026, 10, 20),
            projet=project,
            tache=task,
            heures=Decimal("2.00"),
        )
        draft_sheet = FeuilleTemps.objects.create(
            employe=self.admin_employee,
            semaine_debut=date(2026, 10, 12),
            statut="SOUMISE",
        )
        LigneFeuilleTemps.objects.create(
            feuille=draft_sheet,
            date_travail=date(2026, 10, 14),
            projet=project,
            tache=task,
            heures=Decimal("4.00"),
        )
        Paie.objects.create(
            employe=self.admin_employee,
            periode="2026-10",
            libelle="Paie octobre 2026",
            statut="PAYE",
            salaire_brut=Decimal("400000.00"),
            cout_charge=Decimal("440000.00"),
        )

        response = self.client.get(
            reverse("couts-projets"),
            {"date_debut": "2026-10-01", "date_fin": "2026-10-31"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["totaux"]["heures_validees"], "2.00")
        self.assertEqual(response.data["totaux"]["cout_estime"], "5000.00")
        self.assertTrue(response.data["totaux"]["cout_complet"])
        task_result = response.data["projets"][0]["taches"][0]
        self.assertEqual(task_result["tache_id"], task.pk)
        self.assertEqual(task_result["cout_estime"], "5000.00")

    def test_project_cost_report_marks_missing_tgm_as_incomplete(self):
        project, task = self.create_timesheet_project("TIMESHEET-COST-MISSING")
        sheet = FeuilleTemps.objects.create(
            employe=self.admin_employee,
            semaine_debut=date(2026, 10, 19),
            statut="VALIDEE",
        )
        LigneFeuilleTemps.objects.create(
            feuille=sheet,
            date_travail=date(2026, 10, 20),
            projet=project,
            tache=task,
            heures=Decimal("3.00"),
        )

        response = self.client.get(
            reverse("couts-projets"),
            {"date_debut": "2026-10-01", "date_fin": "2026-10-31"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["totaux"]["heures_sans_tgm"], "3.00")
        self.assertIsNone(response.data["totaux"]["cout_estime"])
        self.assertFalse(response.data["totaux"]["cout_complet"])

    def test_project_cost_report_requires_payroll_read_permission(self):
        reviewer_role = Role.objects.create(nom="COST_REPORT_READER")
        reviewer_role.permissions.add(
            get_permission_by_code("paie.read"),
        )
        reviewer = self.create_employee(
            "COST-READER-001",
            "cost-reader@example.com",
            "COST-READER-SSN",
            reviewer_role,
        )
        self.client.force_authenticate(user=reviewer)

        response = self.client.get(
            reverse("couts-projets"),
            {"date_debut": "2026-10-01", "date_fin": "2026-10-31"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        reviewer_role.permissions.clear()
        response = self.client.get(
            reverse("couts-projets"),
            {"date_debut": "2026-10-01", "date_fin": "2026-10-31"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_editing_a_validated_timesheet_returns_it_to_draft(self):
        project, task = self.create_timesheet_project()
        sheet = FeuilleTemps.objects.create(
            employe=self.admin_employee,
            semaine_debut=date(2026, 10, 19),
            statut="VALIDEE",
        )
        LigneFeuilleTemps.objects.create(
            feuille=sheet,
            date_travail=date(2026, 10, 20),
            projet=project,
            tache=task,
            heures=Decimal("2.00"),
        )
        response = self.client.put(
            reverse("feuille-temps-detail", args=[sheet.pk]),
            {
                "semaine_debut": "2026-10-19",
                "lignes": [
                    {
                        "date_travail": "2026-10-20",
                        "projet": project.pk,
                        "tache": task.pk,
                        "heures": "3.00",
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["statut"], "BROUILLON")

    def test_project_task_and_assignment_routes_are_connected(self):
        project_response = self.client.post(
            reverse("projet-list"),
            {"code": "PROJECT-API-1", "nom": "Projet API"},
            format="json",
        )
        self.assertEqual(
            project_response.status_code,
            status.HTTP_201_CREATED,
            project_response.data,
        )
        project_id = project_response.data["id"]

        task_response = self.client.post(
            reverse("projet-tache-list", args=[project_id]),
            {"code": "TASK-API-1", "nom": "Tâche API"},
            format="json",
        )
        self.assertEqual(
            task_response.status_code,
            status.HTTP_201_CREATED,
            task_response.data,
        )

        assignment_url = reverse(
            "projet-affectation-list",
            args=[project_id],
        )
        assignment_response = self.client.post(
            assignment_url,
            {"employe": self.employee.pk},
            format="json",
        )
        self.assertEqual(
            assignment_response.status_code,
            status.HTTP_201_CREATED,
            assignment_response.data,
        )
        self.assertEqual(
            self.client.get(assignment_url).data[0]["employe"],
            self.employee.pk,
        )

    def test_project_assignment_requires_its_dedicated_permission(self):
        project = Projet.objects.create(
            code="PROJECT-PERMISSION-1",
            nom="Projet permission",
        )
        reader_role = Role.objects.create(nom="PROJECT_READ_ONLY")
        reader_role.permissions.add(get_permission_by_code("projet.read"))
        reader = self.create_employee(
            "PROJECT-READER-001",
            "project-reader-domain@example.com",
            "PROJECT-READER-SSN",
            reader_role,
        )
        self.client.force_authenticate(user=reader)

        response = self.client.post(
            reverse("projet-affectation-list", args=[project.pk]),
            {"employe": self.employee.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_payroll_mass_summary_aggregates_finalized_payrolls_and_filters_department(self):
        self.contract.type.add(self.contract_type)
        second_employee = self.create_employee(
            "EMP-101", "domain-employee-2@example.com", "000000101"
        )
        second_contract = Contrat.objects.create(
            date_debut=date(2024, 1, 1),
            salaire_base="3000.00",
            employe=second_employee,
        )
        second_contract.type.add(self.contract_type)
        Paie.objects.create(
            periode="2026-10", libelle="Validée", salaire_brut="300000",
            salaire_net="250000", cotisations="50000", cout_charge="350000",
            statut="VALIDEE", employe=self.employee,
            detail_calcul={"classification":{"departement":{"id":self.department.pk,"nom":"Administration"},"types_contrat":[{"id":self.contract_type.pk,"type":"CDI"}]}},
        )
        Paie.objects.create(
            periode="2026-10", libelle="Payée", salaire_brut="400000",
            salaire_net="330000", cotisations="70000", cout_charge="470000",
            statut="PAYE", employe=second_employee,
            detail_calcul={"classification":{"departement":{"id":self.department.pk,"nom":"Administration"},"types_contrat":[{"id":self.contract_type.pk,"type":"CDI"}]}},
        )
        Paie.objects.create(
            periode="2026-10", libelle="Brouillon", statut="BROUILLON", employe=self.admin_employee,
        )

        response = self.client.get(
            reverse("masse-salariale"),
            {"periode_debut": "2026-10", "periode_fin": "2026-10"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["totaux"]["paies_validees"], 1)
        self.assertEqual(response.data["totaux"]["paies_payees"], 1)
        self.assertEqual(response.data["totaux"]["brut_valide"], "300000.00")
        self.assertEqual(response.data["totaux"]["brut_paye"], "400000.00")
        self.assertEqual(response.data["par_departement"][0]["departement"], "Administration")
        self.assertEqual(response.data["par_type_contrat"][0]["type_contrat"], "CDI")

        filtered = self.client.get(
            reverse("masse-salariale"),
            {
                "periode_debut": "2026-10",
                "periode_fin": "2026-10",
                "departement": self.department.pk,
            },
        )
        self.assertEqual(filtered.status_code, status.HTTP_200_OK, filtered.data)
        self.assertEqual(filtered.data["totaux"]["paies_validees"], 1)

        historical_department = Departement.objects.create(nom="Nouveau département", code="NEW")
        self.employee.department = historical_department
        self.employee.save(update_fields=["department"])
        self.contract.type.clear()
        self.contract.type.add(self.other_contract_type)
        historical = self.client.get(
            reverse("masse-salariale"),
            {"periode_debut":"2026-10","periode_fin":"2026-10","departement":self.department.pk},
        )
        self.assertEqual(historical.status_code, status.HTTP_200_OK, historical.data)
        self.assertEqual(historical.data["par_departement"][0]["departement"], "Administration")
        self.assertEqual(historical.data["par_type_contrat"][0]["type_contrat"], "CDI")

    def test_payroll_mass_summary_requires_paie_read_permission(self):
        role = Role.objects.create(nom="LECTEUR_PAIE_TEST")
        self.employee.roles.add(role)
        self.client.force_authenticate(user=self.employee)
        response = self.client.get(
            reverse("masse-salariale"),
            {"periode_debut": "2026-10", "periode_fin": "2026-10"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        role.permissions.add(get_permission_by_code("paie.read"))
        response = self.client.get(
            reverse("masse-salariale"),
            {"periode_debut": "2026-10", "periode_fin": "2026-10"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

    def test_payroll_mass_summary_rejects_invalid_or_reversed_periods(self):
        invalid_year = self.client.get(
            reverse("masse-salariale"),
            {"periode_debut": "0000-01", "periode_fin": "2026-12"},
        )
        self.assertEqual(invalid_year.status_code, status.HTTP_400_BAD_REQUEST)

        reversed_period = self.client.get(
            reverse("masse-salariale"),
            {"periode_debut": "2026-12", "periode_fin": "2026-01"},
        )
        self.assertEqual(reversed_period.status_code, status.HTTP_400_BAD_REQUEST)

    def assert_crud(self, list_route, detail_route, payload, updated_payload, field, value):
        response = self.client.post(reverse(list_route), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        object_id = response.data["id"]

        response = self.client.get(reverse(list_route))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(object_id, [item["id"] for item in response.data])

        detail_url = reverse(detail_route, args=[object_id])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.put(detail_url, updated_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data[field], value)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_departement_crud(self):
        self.assert_crud(
            "departement-list",
            "departement-detail",
            {"nom": "Finance", "code": "FIN"},
            {"nom": "Finance RH", "code": "FIN"},
            "nom",
            "Finance RH",
        )

    def test_poste_crud(self):
        self.assert_crud(
            "poste-list",
            "poste-detail",
            {"nom": "Gestionnaire", "description": "Paie"},
            {"nom": "Gestionnaire RH", "description": "Paie"},
            "nom",
            "Gestionnaire RH",
        )

    def test_type_contrat_crud(self):
        self.assert_crud(
            "type-contrat-list",
            "type-contrat-detail",
            {"type": "Stage", "description": "Contrat de stage"},
            {"type": "Alternance", "description": "Contrat en alternance"},
            "type",
            "Alternance",
        )

    def test_type_document_crud(self):
        self.assert_crud(
            "type-document-list",
            "type-document-detail",
            {"code": "RIB", "libelle": "Relevé bancaire", "description": "", "is_active": True},
            {"code": "RIB", "libelle": "Coordonnées bancaires", "description": "", "is_active": True},
            "libelle",
            "Coordonnées bancaires",
        )

    def test_contrat_crud(self):
        payload = {
            "date_debut": "2025-01-01",
            "date_fin": None,
            "salaire_base": "3000.00",
            "heures_journalieres": "8.00",
            "statut": "EN_COURS",
            "employe": self.employee.pk,
            "type": [self.contract_type.pk],
        }
        updated_payload = {**payload, "statut": "CLOS"}
        self.assert_crud(
            "contrat-list",
            "contrat-detail",
            payload,
            updated_payload,
            "statut",
            "CLOS",
        )

    def test_contrat_type_contrat_crud(self):
        self.assert_crud(
            "contrat-type-list",
            "contrat-type-detail",
            {"contrat": self.contract.pk, "type_contrat": self.contract_type.pk},
            {"contrat": self.contract.pk, "type_contrat": self.other_contract_type.pk},
            "type_contrat",
            self.other_contract_type.pk,
        )

    def test_coordonnees_bancaires_crud(self):
        payload = {
            "iban": "FR7630006000011234567890189",
            "bic": "AGRIFRPP",
            "swift": "AGRIFRPP",
            "banque": "Banque A",
            "employe": self.employee.pk,
        }
        updated_payload = {**payload, "banque": "Banque RH"}
        self.assert_crud(
            "coordonnees-bancaires-list",
            "coordonnees-bancaires-detail",
            payload,
            updated_payload,
            "banque",
            "Banque RH",
        )

    def test_demande_absence_crud(self):
        payload = {
            "type_conge": self.leave_type.pk,
            "date_debut": "2025-05-01",
            "date_fin": "2025-05-05",
            "motif": "Repos",
            "statut": "EN_ATTENTE",
            "employe": self.employee.pk,
        }
        updated_payload = {**payload, "motif": "Congé annuel"}
        self.assert_crud(
            "demande-absence-list",
            "demande-absence-detail",
            payload,
            updated_payload,
            "motif",
            "Congé annuel",
        )

    def test_document_crud(self):
        payload = {
            "type_document": self.document_type.pk,
            "fichier": "attestation.pdf",
            "date_depot": "2025-01-10",
            "date_expiration": None,
            "employes": [self.employee.pk],
        }
        updated_payload = {**payload, "fichier": "attestation-rh.pdf"}
        self.assert_crud(
            "document-list",
            "document-detail",
            payload,
            updated_payload,
            "fichier",
            "attestation-rh.pdf",
        )

    def test_document_employe_crud(self):
        payload = {"document": self.document.pk, "employe": self.employee.pk}
        self.assert_crud(
            "document-employe-list",
            "document-employe-detail",
            payload,
            payload,
            "employe",
            self.employee.pk,
        )

    def test_ordre_virement_crud(self):
        for period in ("2025-01", "2025-02"):
            Paie.objects.create(employe=self.employee, periode=period, libelle="Paie validée pour ordre", statut="VALIDEE")
        payload = {
            "periode": "2025-01",
            "statut": "GENERE",
            "date_generation": "2025-01-31T12:00:00Z",
            "date_traitement": None,
            "employe": self.employee.pk,
        }
        updated_payload = {**payload, "periode": "2025-02"}
        updated_payload.pop("statut")
        updated_payload.pop("date_traitement")
        self.assert_crud(
            "ordre-virement-list",
            "ordre-virement-detail",
            payload,
            updated_payload,
            "periode",
            "2025-02",
        )

    def test_transfer_state_changes_only_through_actions(self):
        Paie.objects.create(employe=self.employee, periode="2025-03", libelle="Paie validée pour ordre", statut="VALIDEE")
        response = self.client.post(
            reverse("ordre-virement-list"),
            {
                "periode": "2025-03",
                "statut": "TRAITE",
                "date_generation": "2025-03-31T12:00:00Z",
                "date_traitement": "2025-04-01T12:00:00Z",
                "employe": self.employee.pk,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        create_response = self.client.post(
            reverse("ordre-virement-list"),
            {
                "periode": "2025-03",
                "date_generation": "2025-03-31T12:00:00Z",
                "employe": self.employee.pk,
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        order_id = create_response.data["id"]
        self.assertEqual(create_response.data["statut"], "GENERE")
        self.assertIsNone(create_response.data["date_traitement"])

        treat_response = self.client.post(
            reverse("ordre-virement-traiter", args=[order_id]), {}, format="json"
        )
        self.assertEqual(treat_response.status_code, status.HTTP_200_OK, treat_response.data)
        self.assertEqual(treat_response.data["statut"], "TRAITE")
        self.assertIsNotNone(treat_response.data["date_traitement"])

        repeat_response = self.client.post(
            reverse("ordre-virement-traiter", args=[order_id]), {}, format="json"
        )
        self.assertEqual(repeat_response.status_code, status.HTTP_400_BAD_REQUEST)

        update_response = self.client.put(
            reverse("ordre-virement-detail", args=[order_id]),
            {**create_response.data, "statut": "GENERE"},
            format="json",
        )
        self.assertEqual(update_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_payroll_evolution_endpoint_supports_monthly_and_annual_granularity(self):
        Paie.objects.create(
            periode="2025-12", libelle="Paie démo annuelle", salaire_brut="100000",
            salaire_net="80000", cotisations="20000", cout_charge="120000",
            statut="PAYE", employe=self.employee,
            detail_calcul={"classification":{"departement":{"id":self.department.pk,"nom":"Administration"},"types_contrat":[]}},
        )
        for granularity, expected_key in (("mensuelle", "periode"), ("annuelle", "annee")):
            response = self.client.get(
                reverse("masse-salariale-evolution"),
                {"periode_debut":"2025-01","periode_fin":"2025-12","granularite":granularity},
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
            self.assertEqual(response.data["granularite"], granularity)
            self.assertIn(expected_key, response.data["evolution"][0])

    def test_paie_crud(self):
        payload = {
            "periode": "2025-01",
            "libelle": "Paie janvier",
            "employe": self.employee.pk,
        }
        updated_payload = {**payload, "libelle": "Paie janvier brouillon mise à jour"}
        self.assert_crud(
            "paie-list",
            "paie-detail",
            payload,
            updated_payload,
            "libelle",
            "Paie janvier brouillon mise à jour",
        )

    def test_paie_can_be_created_as_draft_before_transfer_and_calculation(self):
        response = self.client.post(
            reverse("paie-list"),
            {
                "periode": "2026-10",
                "libelle": "Brouillon octobre",
                "employe": self.employee.pk,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data["statut"], "BROUILLON")
        self.assertEqual(response.data["devise"], "XOF")
        self.assertEqual(response.data["detail_calcul"], {})
        self.assertIsNone(response.data["salaire_brut"])
        self.assertIsNone(response.data["salaire_net"])
        self.assertIsNone(response.data["date_calcul"])
        self.assertIsNone(response.data["ordre_virement"])

    def test_paie_rejects_manual_calculated_fields(self):
        response = self.client.post(
            reverse("paie-list"),
            {
                "periode": "2026-10",
                "libelle": "Paie saisie",
                "salaire_base": "300000.00",
                "salaire_brut": "320000.00",
                "salaire_net": "250000.00",
                "cout_charge": "360000.00",
                "cotisations": "70000.00",
                "statut": "CALCULE",
                "employe": self.employee.pk,
                "ordre_virement": self.transfer.pk,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIn("salaire_net", response.data)

    def test_paie_requires_year_and_month_period(self):
        response = self.client.post(
            reverse("paie-list"),
            {
                "periode": "octobre-2026",
                "libelle": "Brouillon octobre",
                "employe": self.employee.pk,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("periode", response.data)

    def test_payroll_calculation_uses_test_rules_variables_and_unpaid_absence(self):
        self.contract.salaire_base = Decimal("300000.00")
        self.contract.save(update_fields=["salaire_base"])
        self.contract.type.add(self.contract_type)
        unpaid_type = TypeConge.objects.create(
            code="TEST-SANS-SOLDE",
            libelle="Absence non rémunérée de test",
            est_payant=False,
        )
        DemandeAbsence.objects.create(
            employe=self.employee,
            type_conge=unpaid_type,
            date_debut=date(2026, 10, 5),
            date_fin=date(2026, 10, 6),
            motif="Test fictif",
            statut="VALIDEE",
        )
        paid_type = TypeConge.objects.create(
            code="TEST-PAYE",
            libelle="Congé payé fictif",
            est_payant=True,
        )
        DemandeAbsence.objects.create(
            employe=self.employee,
            type_conge=paid_type,
            date_debut=date(2026, 10, 7),
            date_fin=date(2026, 10, 7),
            motif="Congé payé fictif",
            statut="VALIDEE",
        )

        rule_response = self.client.post(
            reverse("regle-paie-list"),
            {
                "code": "TEST-BF-2026",
                "nom": "Règles fictives de test",
                "pays": "BF",
                "devise": "XOF",
                "date_debut": "2026-01-01",
                "date_fin": None,
                "heures_mensuelles": "173.33",
                "plafond_cnss": "800000.00",
                "taux_cnss_salarial": "0.050000",
                "taux_cnss_patronal": "0.160000",
                "taux_tpa_patronal": "0.030000",
                "abattement_professionnel": "0.200000",
                "plafond_deduction_retraite": "0.080000",
                "tranches_iuts": [
                    {"minimum": "0", "maximum": "100000", "taux": "0"},
                    {"minimum": "100000", "maximum": None, "taux": "0.10"},
                ],
                "reductions_iuts_charges": [
                    {"charges": 1, "taux": "0.08"},
                ],
                "source_reference": "Paramètres de test isolé",
            },
            format="json",
        )
        self.assertEqual(rule_response.status_code, status.HTTP_201_CREATED, rule_response.data)
        rule_validation_response = self.client.post(
            reverse("regle-paie-valider", args=[rule_response.data["id"]]),
            {},
            format="json",
        )
        self.assertEqual(
            rule_validation_response.status_code,
            status.HTTP_200_OK,
        )

        for element in (
            {
                "employe": self.employee.pk,
                "periode": "2026-10",
                "nature": "PRIME",
                "libelle": "Prime fictive",
                "montant": "20000.00",
                "soumis_iuts": True,
                "soumis_cnss": True,
                "verse_en_especes": True,
            },
            {
                "employe": self.employee.pk,
                "periode": "2026-10",
                "nature": "HEURE_SUP",
                "libelle": "Heures supplémentaires fictives",
                "montant": None,
                "quantite": "10.00",
                "coefficient": "1.5000",
                "soumis_iuts": True,
                "soumis_cnss": True,
                "verse_en_especes": True,
            },
        ):
            response = self.client.post(
                reverse("element-variable-paie-list"),
                element,
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
            self.assertFalse(response.data["valide"])
            validation_response = self.client.post(
                reverse(
                    "element-variable-paie-valider",
                    args=[response.data["id"]],
                ),
                {},
                format="json",
            )
            self.assertEqual(
                validation_response.status_code,
                status.HTTP_200_OK,
                validation_response.data,
            )
            self.assertTrue(validation_response.data["valide"])

        paie_response = self.client.post(
            reverse("paie-list"),
            {
                "periode": "2026-10",
                "libelle": "Paie fictive octobre",
                "employe": self.employee.pk,
            },
            format="json",
        )
        self.assertEqual(paie_response.status_code, status.HTTP_201_CREATED, paie_response.data)

        response = self.client.post(
            reverse("paie-calculer", args=[paie_response.data["id"]]),
            {
                "regle_paie": rule_response.data["id"],
                "charges_familiales": 1,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        detail = response.data["detail_calcul"]
        self.assertEqual(detail["version_schema"], 2)
        self.assertEqual(
            detail["classification"],
            {
                "departement": {"id": self.department.pk, "nom": "Administration"},
                "types_contrat": [{"id": self.contract_type.pk, "type": "CDI"}],
            },
        )
        base = Decimal("300000") * Decimal("20") / Decimal("22")
        overtime = Decimal("300000") / Decimal("173.33") * Decimal("10") * Decimal("1.5")
        cnss_base = base + overtime + Decimal("20000")
        expected_gross = (cnss_base).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        expected_employee_cnss = (
            cnss_base * Decimal("0.05")
        ).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        iuts_base = max(
            Decimal("0"),
            cnss_base - expected_employee_cnss - base * Decimal("0.20"),
        )
        iuts_before_reduction = max(Decimal("0"), iuts_base - Decimal("100000")) * Decimal("0.10")
        expected_iuts = (
            iuts_before_reduction * Decimal("0.92")
        ).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        expected_net = expected_gross - expected_employee_cnss - expected_iuts

        self.assertEqual(response.data["statut"], "CALCULE")
        self.assertEqual(response.data["devise"], "XOF")
        self.assertEqual(Decimal(response.data["salaire_brut"]), expected_gross)
        self.assertEqual(Decimal(response.data["salaire_net"]), expected_net)
        self.assertEqual(detail["contrat"]["jours_absence_non_payee"], 2)
        self.assertEqual(detail["contrat"]["jours_absence_payee"], 1)
        self.assertEqual(detail["contrat"]["jours_payes"], 20)
        self.assertEqual(detail["iuts"]["charges_familiales"], 1)
        self.assertNotIn("est_fictif", detail["regle"])
        self.assertTrue(detail["regle"]["valide"])

        changed_department = Departement.objects.create(nom="Service modifié", code="MOD")
        self.employee.department = changed_department
        self.employee.save(update_fields=["department"])
        self.contract.type.clear()
        self.contract.type.add(self.other_contract_type)
        paie_after_changes = Paie.objects.get(pk=paie_response.data["id"])
        self.assertEqual(
            paie_after_changes.detail_calcul["classification"]["departement"]["nom"],
            "Administration",
        )
        self.assertEqual(
            paie_after_changes.detail_calcul["classification"]["types_contrat"][0]["type"],
            "CDI",
        )

        recalculation_response = self.client.post(
            reverse("paie-calculer", args=[paie_response.data["id"]]),
            {
                "regle_paie": rule_response.data["id"],
                "charges_familiales": 1,
            },
            format="json",
        )
        self.assertEqual(recalculation_response.status_code, status.HTTP_400_BAD_REQUEST)

        validation_response = self.client.post(
            reverse("paie-valider", args=[paie_response.data["id"]]),
            {},
            format="json",
        )
        self.assertEqual(validation_response.status_code, status.HTTP_200_OK)
        self.assertEqual(validation_response.data["statut"], "VALIDEE")

        pending_order = OrdreVirement.objects.create(
            periode="2026-10",
            statut="GENERE",
            date_generation=timezone.now(),
            employe=self.employee,
        )
        premature_payment = self.client.post(
            reverse("paie-marquer-payee", args=[paie_response.data["id"]]),
            {"ordre_virement": pending_order.pk},
            format="json",
        )
        self.assertEqual(premature_payment.status_code, status.HTTP_400_BAD_REQUEST)

        processed_order = OrdreVirement.objects.create(
            periode="2026-10",
            statut="GENERE",
            date_generation=timezone.now(),
            employe=self.employee,
        )
        processed_order_response = self.client.post(
            reverse("ordre-virement-traiter", args=[processed_order.pk]),
            {},
            format="json",
        )
        self.assertEqual(processed_order_response.status_code, status.HTTP_200_OK)
        payment_response = self.client.post(
            reverse("paie-marquer-payee", args=[paie_response.data["id"]]),
            {"ordre_virement": processed_order.pk},
            format="json",
        )
        self.assertEqual(payment_response.status_code, status.HTTP_200_OK)
        self.assertEqual(payment_response.data["statut"], "PAYE")

    def test_payroll_calculation_rejects_paid_and_unpaid_absence_overlap(self):
        unpaid_type = TypeConge.objects.create(
            code="TEST-UNPAID-OVERLAP",
            libelle="Absence non payée",
            est_payant=False,
        )
        paid_type = TypeConge.objects.create(
            code="TEST-PAID-OVERLAP",
            libelle="Congé payé",
            est_payant=True,
        )
        DemandeAbsence.objects.create(
            employe=self.employee,
            type_conge=unpaid_type,
            date_debut=date(2026, 10, 12),
            date_fin=date(2026, 10, 13),
            motif="Sans solde",
            statut="VALIDEE",
        )
        DemandeAbsence.objects.create(
            employe=self.employee,
            type_conge=paid_type,
            date_debut=date(2026, 10, 13),
            date_fin=date(2026, 10, 14),
            motif="Congé payé",
            statut="VALIDEE",
        )
        paie = Paie.objects.create(
            periode="2026-10",
            libelle="Paie avec absences incohérentes",
            employe=self.employee,
        )
        rule = ReglePaie.objects.create(
            code="TEST-OVERLAP-RULE",
            nom="Règle fictive chevauchement",
            pays="BF",
            devise="XOF",
            date_debut=date(2026, 1, 1),
            heures_mensuelles=Decimal("173.33"),
            plafond_cnss=Decimal("800000"),
            taux_cnss_salarial=Decimal("0.05"),
            taux_cnss_patronal=Decimal("0.16"),
            taux_tpa_patronal=Decimal("0.03"),
            abattement_professionnel=Decimal("0.20"),
            plafond_deduction_retraite=Decimal("0.08"),
            tranches_iuts=[{"minimum": "0", "maximum": None, "taux": "0"}],
            reductions_iuts_charges=[],
            source_reference="Paramètres de test isolé",
            valide=True,
        )

        response = self.client.post(
            reverse("paie-calculer", args=[paie.pk]),
            {"regle_paie": rule.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("absences", response.data)

    def test_a_transfer_order_cannot_be_reused_for_another_payroll(self):
        first_payroll = Paie.objects.create(
            periode="2026-08",
            libelle="Première paie",
            salaire_base=Decimal("300000"),
            salaire_brut=Decimal("300000"),
            salaire_net=Decimal("250000"),
            cotisations=Decimal("50000"),
            cout_charge=Decimal("330000"),
            statut="VALIDEE",
            employe=self.employee,
        )
        order = OrdreVirement.objects.create(
            periode=first_payroll.periode,
            statut="GENERE",
            date_generation=timezone.now(),
            employe=self.employee,
        )
        processed = self.client.post(
            reverse("ordre-virement-traiter", args=[order.pk]), {}, format="json"
        )
        self.assertEqual(processed.status_code, status.HTTP_200_OK)
        paid = self.client.post(
            reverse("paie-marquer-payee", args=[first_payroll.pk]),
            {"ordre_virement": order.pk},
            format="json",
        )
        self.assertEqual(paid.status_code, status.HTTP_200_OK, paid.data)

        second_payroll = Paie.objects.create(
            periode="2026-09",
            libelle="Deuxième paie",
            salaire_base=Decimal("300000"),
            salaire_brut=Decimal("300000"),
            salaire_net=Decimal("250000"),
            cotisations=Decimal("50000"),
            cout_charge=Decimal("330000"),
            statut="VALIDEE",
            employe=self.employee,
        )
        response = self.client.post(
            reverse("paie-marquer-payee", args=[second_payroll.pk]),
            {"ordre_virement": order.pk},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("ordre_virement", response.data)

    def test_complete_payroll_contract_and_transfer_flow(self):
        contract_response = self.client.put(
            reverse("contrat-detail", args=[self.contract.pk]),
            {
                "date_debut": "2024-01-01",
                "date_fin": None,
                "salaire_base": "300000.00",
                "heures_journalieres": "8.00",
                "statut": "EN_COURS",
                "employe": self.employee.pk,
                "type": [],
            },
            format="json",
        )
        self.assertEqual(contract_response.status_code, status.HTTP_200_OK, contract_response.data)

        rule_response = self.client.post(
            reverse("regle-paie-list"),
            {
                "code": "E2E-FICTIVE-2026",
                "nom": "Profil fictif E2E",
                "pays": "BF",
                "devise": "XOF",
                "date_debut": "2026-01-01",
                "date_fin": None,
                "actif": True,
                "heures_mensuelles": "173.33",
                "jours_ouvres_semaine": 5,
                "decimales_montant": 0,
                "plafond_cnss": "800000",
                "taux_cnss_salarial": "0.05",
                "taux_cnss_patronal": "0.16",
                "taux_tpa_patronal": "0.03",
                "abattement_professionnel": "0.20",
                "plafond_deduction_retraite": "0.08",
                "tranches_iuts": [
                    {"minimum": "0", "maximum": "100000", "taux": "0"},
                    {"minimum": "100000", "maximum": None, "taux": "0.10"},
                ],
                "reductions_iuts_charges": [{"charges": 1, "taux": "0.08"}],
                "source_reference": "Paramètres de test isolé",
            },
            format="json",
        )
        self.assertEqual(rule_response.status_code, status.HTTP_201_CREATED, rule_response.data)
        validated_rule = self.client.post(
            reverse("regle-paie-valider", args=[rule_response.data["id"]]), {}, format="json",
        )
        self.assertEqual(validated_rule.status_code, status.HTTP_200_OK)

        payroll_response = self.client.post(
            reverse("paie-list"),
            {
                "periode": "2026-10",
                "libelle": "Paie fictive E2E octobre",
                "employe": self.employee.pk,
            },
            format="json",
        )
        self.assertEqual(payroll_response.status_code, status.HTTP_201_CREATED, payroll_response.data)

        calculation_response = self.client.post(
            reverse("paie-calculer", args=[payroll_response.data["id"]]),
            {"regle_paie": rule_response.data["id"], "charges_familiales": 1},
            format="json",
        )
        self.assertEqual(calculation_response.status_code, status.HTTP_200_OK, calculation_response.data)
        self.assertEqual(calculation_response.data["statut"], "CALCULE")
        self.assertIsNotNone(calculation_response.data["salaire_net"])

        validate_response = self.client.post(
            reverse("paie-valider", args=[payroll_response.data["id"]]), {}, format="json",
        )
        self.assertEqual(validate_response.status_code, status.HTTP_200_OK)
        self.assertEqual(validate_response.data["statut"], "VALIDEE")

        order_response = self.client.post(
            reverse("ordre-virement-list"),
            {
                "periode": "2026-10",
                "date_generation": "2026-10-20T10:00:00Z",
                "employe": self.employee.pk,
            },
            format="json",
        )
        self.assertEqual(order_response.status_code, status.HTTP_201_CREATED, order_response.data)
        self.assertEqual(order_response.data["statut"], "GENERE")

        processed_order_response = self.client.post(
            reverse("ordre-virement-traiter", args=[order_response.data["id"]]),
            {},
            format="json",
        )
        self.assertEqual(processed_order_response.status_code, status.HTTP_200_OK)
        self.assertEqual(processed_order_response.data["statut"], "TRAITE")
        self.assertIsNotNone(processed_order_response.data["date_traitement"])

        duplicate_order = self.client.post(
            reverse("ordre-virement-list"),
            {
                "periode": "2026-10",
                "date_generation": "2026-10-20T10:00:00Z",
                "employe": self.employee.pk,
            },
            format="json",
        )
        self.assertEqual(duplicate_order.status_code, status.HTTP_400_BAD_REQUEST)
        paid_response = self.client.post(
            reverse("paie-marquer-payee", args=[payroll_response.data["id"]]),
            {"ordre_virement": order_response.data["id"]},
            format="json",
        )
        self.assertEqual(paid_response.status_code, status.HTTP_200_OK, paid_response.data)
        self.assertEqual(paid_response.data["statut"], "PAYE")

    def test_payslip_pdf_is_generated_privately_and_downloaded_by_employee(self):
        paie = Paie.objects.create(
            periode="2026-11",
            libelle="Salaire mensuel",
            salaire_base=Decimal("300000"),
            salaire_brut=Decimal("320000"),
            salaire_net=Decimal("273500"),
            cotisations=Decimal("72000"),
            cout_charge=Decimal("357000"),
            detail_calcul={
                "totaux": {
                    "salaire_base": "300000",
                    "salaire_brut": "320000",
                    "salaire_net": "273500",
                    "cout_charge": "357000",
                    "retenues_salariales_diverses": "5000",
                    "avantages_non_verses": "0",
                },
                "cotisations": {
                    "cnss_salariale": "15000",
                    "cnss_patronale": "48000",
                    "tpa_patronale": "9000",
                    "autres_charges_patronales": "0",
                },
                "iuts": {"net": "6500"},
                "elements": [
                    {
                        "nature": "PRIME",
                        "libelle": "Prime de rendement",
                        "montant": "20000",
                    },
                    {
                        "nature": "RETENUE",
                        "libelle": "Avance sur salaire",
                        "montant": "5000",
                    },
                ],
            },
            statut="VALIDEE",
            date_calcul=timezone.now(),
            employe=self.employee,
        )

        generated = self.client.post(
            reverse("paie-bulletin", args=[paie.pk]), {}, format="json"
        )
        self.assertEqual(generated.status_code, status.HTTP_200_OK, generated.data)
        paie.refresh_from_db()
        self.assertTrue(paie.bulletin_pdf)
        self.assertTrue(paie.bulletin_pdf.path.startswith(str(paie.bulletin_pdf.storage.location)))

        self.client.force_authenticate(user=self.employee)
        downloaded = self.client.get(reverse("paie-bulletin", args=[paie.pk]), HTTP_ACCEPT="*/*")
        self.assertEqual(downloaded.status_code, status.HTTP_200_OK)
        self.assertEqual(downloaded["Content-Type"], "application/pdf")
        self.assertIn("private", downloaded["Cache-Control"])
        self.assertTrue(b"%PDF" in b"".join(downloaded.streaming_content))

        paie.bulletin_pdf.delete(save=False)

    def test_validated_real_payroll_can_be_marked_paid_by_matching_processed_order(self):
        paie = Paie.objects.create(
            periode="2026-08",
            libelle="Paie de test validée",
            salaire_base=Decimal("300000"),
            salaire_brut=Decimal("300000"),
            salaire_net=Decimal("250000"),
            cotisations=Decimal("50000"),
            cout_charge=Decimal("330000"),
            statut="VALIDEE",
            employe=self.employee,
        )
        ordre = OrdreVirement.objects.create(
            periode=paie.periode,
            statut="GENERE",
            date_generation=timezone.now(),
            employe=self.employee,
        )
        ordre_response = self.client.post(
            reverse("ordre-virement-traiter", args=[ordre.pk]),
            {},
            format="json",
        )
        self.assertEqual(ordre_response.status_code, status.HTTP_200_OK)

        response = self.client.post(
            reverse("paie-marquer-payee", args=[paie.pk]),
            {"ordre_virement": ordre.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["statut"], "PAYE")
        self.assertEqual(response.data["ordre_virement"], ordre.pk)
        self.assertIsNotNone(response.data["date_paiement"])

    def test_payroll_calculation_requires_a_configured_rule_profile(self):
        paie_response = self.client.post(
            reverse("paie-list"),
            {
                "periode": "2026-10",
                "libelle": "Paie sans règle",
                "employe": self.employee.pk,
            },
            format="json",
        )

        response = self.client.post(
            reverse("paie-calculer", args=[paie_response.data["id"]]),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("regle_paie", response.data)

    def test_payroll_rule_requires_explicit_rates(self):
        response = self.client.post(
            reverse("regle-paie-list"),
            {
                "code": "TEST-RULE-INCOMPLETE",
                "nom": "Profil incomplet",
                "pays": "BF",
                "devise": "XOF",
                "date_debut": "2026-01-01",
                "heures_mensuelles": "173.33",
                "plafond_cnss": "800000",
                "tranches_iuts": [
                    {"minimum": "0", "maximum": None, "taux": "0"},
                ],
                "source_reference": "Paramètres de test isolé",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("taux_cnss_salarial", response.data)

    def test_real_payroll_rule_requires_a_source_reference(self):
        response = self.client.post(
            reverse("regle-paie-list"),
            {
                "code": "TEST-RULE-REAL-UNSOURCED",
                "nom": "Profil sans source",
                "pays": "BF",
                "devise": "XOF",
                "date_debut": "2026-01-01",
                "heures_mensuelles": "173.33",
                "plafond_cnss": "800000",
                "taux_cnss_salarial": "0.05",
                "taux_cnss_patronal": "0.16",
                "taux_tpa_patronal": "0.03",
                "abattement_professionnel": "0.20",
                "plafond_deduction_retraite": "0.08",
                "tranches_iuts": [
                    {"minimum": "0", "maximum": None, "taux": "0"},
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("source_reference", response.data)

    def test_variable_cannot_be_self_validated_in_creation_payload(self):
        response = self.client.post(
            reverse("element-variable-paie-list"),
            {
                "employe": self.employee.pk,
                "periode": "2026-10",
                "nature": "PRIME",
                "libelle": "Prime non approuvée",
                "montant": "10000",
                "soumis_iuts": True,
                "soumis_cnss": True,
                "valide": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("valide", response.data)

    def test_duplicate_payroll_for_employee_and_period_is_rejected(self):
        first_response = self.client.post(
            reverse("paie-list"),
            {
                "periode": "2026-11",
                "libelle": "Première paie",
                "employe": self.employee.pk,
            },
            format="json",
        )
        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)

        duplicate_response = self.client.post(
            reverse("paie-list"),
            {
                "periode": "2026-11",
                "libelle": "Deuxième paie",
                "employe": self.employee.pk,
            },
            format="json",
        )

        self.assertEqual(duplicate_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("periode", duplicate_response.data)

    def test_cancelled_payroll_records_reason_and_allows_replacement(self):
        draft_response = self.client.post(
            reverse("paie-list"),
            {
                "periode": "2026-09",
                "libelle": "Paie à annuler",
                "employe": self.employee.pk,
            },
            format="json",
        )
        self.assertEqual(draft_response.status_code, status.HTTP_201_CREATED)

        cancellation_response = self.client.post(
            reverse("paie-annuler", args=[draft_response.data["id"]]),
            {"motif": "Erreur de saisie fictive"},
            format="json",
        )
        self.assertEqual(cancellation_response.status_code, status.HTTP_200_OK)
        self.assertEqual(cancellation_response.data["statut"], "ANNULE")
        self.assertEqual(
            cancellation_response.data["motif_annulation"],
            "Erreur de saisie fictive",
        )
        self.assertEqual(cancellation_response.data["annule_par"], self.admin_employee.pk)

        replacement_response = self.client.post(
            reverse("paie-list"),
            {
                "periode": "2026-09",
                "libelle": "Paie corrigée",
                "employe": self.employee.pk,
            },
            format="json",
        )
        self.assertEqual(replacement_response.status_code, status.HTTP_201_CREATED)

    def test_calcul_payroll_requires_update_permission(self):
        role = Role.objects.create(nom="PAIE_CREATION_SEULE")
        role.permissions.add(
            get_permission_by_code("paie.read"),
            get_permission_by_code("paie.create"),
        )
        self.employee.roles.add(role)
        self.client.force_authenticate(user=self.employee)
        response = self.client.post(
            reverse("paie-list"),
            {
                "periode": "2026-12",
                "libelle": "Paie brouillon",
                "employe": self.employee.pk,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        calculation_response = self.client.post(
            reverse("paie-calculer", args=[response.data["id"]]),
            {},
            format="json",
        )

        self.assertEqual(calculation_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_crud(self):
        self.assert_crud(
            "permission-list",
            "permission-detail",
            {"nom": "Gérer les contrats", "code": "contract.manage"},
            {"nom": "Gestion des contrats", "code": "contract.manage"},
            "nom",
            "Gestion des contrats",
        )

    def test_permission_api_uses_and_deletes_auth_permission_ids(self):
        response = self.client.post(
            reverse("permission-list"),
            {"nom": "Gérer les rôles", "code": "role.manage"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        permission_id = response.data["id"]
        auth_permission = AuthPermission.objects.get(pk=permission_id)
        self.assertEqual(auth_permission.codename, "manage")
        self.assertEqual(auth_permission.content_type.app_label, "core")

        delete_response = self.client.delete(
            reverse("permission-detail", args=[permission_id])
        )

        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(AuthPermission.objects.filter(pk=permission_id).exists())

    def test_role_crud(self):
        self.assert_crud(
            "role-list",
            "role-detail",
            {"nom": "GESTIONNAIRE_RH", "description": "", "permissions": []},
            {"nom": "GESTIONNAIRE_RH", "description": "Gestionnaire RH", "permissions": []},
            "description",
            "Gestionnaire RH",
        )
