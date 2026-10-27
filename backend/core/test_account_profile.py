from django.urls import reverse
from rest_framework.test import APITestCase
from core.models import Employe


class AccountProfileTests(APITestCase):
    def setUp(self):
        self.old_password = "Initial-Secret-2026!"
        self.user = self.employee("ONE")
        self.other = self.employee("TWO")
        self.client.force_authenticate(self.user)

    def employee(self, suffix):
        return Employe.objects.create_user(email=f"profile-{suffix.lower()}@example.com", password=self.old_password,
            matricule=f"PROFILE-{suffix}", nom="Nom", prenom="Prenom", date_naissance="1990-01-01",
            adresse="Test", telephone="000", num_secu_sociale=f"PROFILE-SSN-{suffix}", date_entree="2020-01-01")

    def password_payload(self, **changes):
        return {"ancien_mot_de_passe": self.old_password, "nouveau_mot_de_passe": "Nouveau-Secret-2026!",
            "confirmation": "Nouveau-Secret-2026!", **changes}

    def test_authenticated_employee_without_management_rights_can_update_only_own_name(self):
        response = self.client.patch(reverse("auth-current-user"), {"nom": "Traoré", "prenom": "Awa"}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["nom"], "Traoré")
        self.assertEqual(response.data["prenom"], "Awa")
        self.assertNotIn("password", response.data)
        self.user.refresh_from_db()
        self.other.refresh_from_db()
        self.assertEqual(self.user.nom, "Traoré")
        self.assertEqual(self.other.nom, "Nom")
        self.assertEqual(response.data["permissions"], [])

    def test_profile_rejects_privileged_fields_and_other_employee_ids(self):
        for field, value in (("id", self.other.pk), ("roles", []), ("is_staff", True),
                ("is_superuser", True), ("email", self.other.email), ("password", "Changed!123")):
            response = self.client.patch(reverse("auth-current-user"), {"nom": "Forbidden", field: value}, format="json")
            self.assertEqual(response.status_code, 400, response.data)
        self.user.refresh_from_db()
        self.assertEqual(self.user.nom, "Nom")

    def test_profile_rejects_blank_names(self):
        self.assertEqual(self.client.patch(reverse("auth-current-user"), {"nom": " "}, format="json").status_code, 400)

    def test_profile_and_password_require_authentication(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.patch(reverse("auth-current-user"), {"nom": "Name"}, format="json").status_code, 401)
        self.assertEqual(self.client.post(reverse("auth-change-password"), self.password_payload(), format="json").status_code, 401)

    def test_password_rejects_wrong_current_password_mismatch_weak_and_same_password(self):
        cases = [
            self.password_payload(ancien_mot_de_passe="Incorrect"),
            self.password_payload(confirmation="Different"),
            self.password_payload(nouveau_mot_de_passe="123", confirmation="123"),
            self.password_payload(nouveau_mot_de_passe=self.old_password, confirmation=self.old_password),
        ]
        for payload in cases:
            response = self.client.post(reverse("auth-change-password"), payload, format="json")
            self.assertEqual(response.status_code, 400, response.data)
            self.user.refresh_from_db()
            self.assertTrue(self.user.check_password(self.old_password))

    def test_password_change_hashes_password_and_new_login_replaces_old_credentials(self):
        response = self.client.post(reverse("auth-change-password"), self.password_payload(), format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.password, "Nouveau-Secret-2026!")
        self.other.refresh_from_db()
        self.assertTrue(self.other.check_password(self.old_password))
        self.client.force_authenticate(None)
        for password, expected in ((self.old_password, 401), ("Nouveau-Secret-2026!", 200)):
            login = self.client.post(reverse("auth-login"), {"email": self.user.email, "password": password}, format="json")
            self.assertEqual(login.status_code, expected, login.data)
            if expected == 200:
                self.assertEqual(login.data["user"]["nom"], self.user.nom)
