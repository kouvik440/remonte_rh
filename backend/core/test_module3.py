from datetime import date

from django.urls import reverse
from rest_framework.test import APITestCase

from core.models import Document, DocumentEmploye, Employe, Role, TypeDocument
from core.permission_codes import get_permission_by_code


class Module3DocumentAccessTests(APITestCase):
    def setUp(self):
        self.owner = self.create_employee("OWNER")
        self.other = self.create_employee("OTHER")
        self.manager = self.create_employee("MANAGER")
        reader = Role.objects.create(nom="M3_READER")
        reader.permissions.add(*[get_permission_by_code(code) for code in (
            "document.read", "document.create", "document.update", "document.delete",
            "document_employe.read", "document_employe.create",
        )])
        self.owner.roles.add(reader)
        manager_role = Role.objects.create(nom="M3_MANAGER")
        manager_role.permissions.add(*[get_permission_by_code(code) for code in (
            "document.manage", "document.read", "document.create", "document.update", "document.delete",
            "type_document.create", "type_document.update", "type_document.delete",
            "document_employe.read", "document_employe.create", "document_employe.update", "document_employe.delete",
        )])
        self.manager.roles.add(manager_role)
        self.type = TypeDocument.objects.create(code="TEST-DOC", libelle="Justificatif fictif")
        self.own_document = self.create_document(self.owner, "reference-owner")
        self.other_document = self.create_document(self.other, "reference-other")
        self.client.force_authenticate(user=self.owner)

    def create_employee(self, code):
        return Employe.objects.create_user(
            email=f"m3-{code.lower()}@example.com", password="TestPassword123!",
            matricule=f"M3-{code}", nom="Test", prenom=code,
            date_naissance=date(1990, 1, 1), date_entree=date(2020, 1, 1),
            adresse="Adresse fictive", telephone="00000000", num_secu_sociale=f"M3-SSN-{code}",
        )

    def create_document(self, employee, reference):
        document = Document.objects.create(type_document=self.type, fichier=reference, date_depot=date(2026, 10, 23))
        document.employes.add(employee)
        return document

    def test_employee_lists_only_own_documents_and_links(self):
        documents = self.client.get(reverse("document-list"))
        links = self.client.get(reverse("document-employe-list"))
        self.assertEqual(documents.status_code, 200)
        self.assertEqual([row["id"] for row in documents.data], [self.own_document.pk])
        self.assertEqual(links.status_code, 200)
        self.assertEqual({row["employe"] for row in links.data}, {self.owner.pk})

    def test_employee_cannot_read_another_document_or_link(self):
        document = self.client.get(reverse("document-detail", args=[self.other_document.pk]))
        link = DocumentEmploye.objects.get(document=self.other_document)
        response = self.client.get(reverse("document-employe-detail", args=[link.pk]))
        self.assertEqual(document.status_code, 403)
        self.assertEqual(response.status_code, 403)

    def test_crud_permission_alone_cannot_modify_documents_or_associations(self):
        payload = {"type_document": self.type.pk, "fichier": "new", "date_depot": "2026-10-23", "employes": [self.other.pk]}
        created = self.client.post(reverse("document-list"), payload, format="json")
        updated = self.client.put(reverse("document-detail", args=[self.own_document.pk]), payload, format="json")
        deleted = self.client.delete(reverse("document-detail", args=[self.own_document.pk]))
        linked = self.client.post(reverse("document-employe-list"), {"document": self.other_document.pk, "employe": self.owner.pk}, format="json")
        self.assertEqual([created.status_code, updated.status_code, deleted.status_code, linked.status_code], [403] * 4)
        self.assertFalse(DocumentEmploye.objects.filter(document=self.other_document, employe=self.owner).exists())

    def test_manager_can_manage_reference_and_employee_associations(self):
        self.client.force_authenticate(user=self.manager)
        created = self.client.post(reverse("document-list"), {
            "type_document": self.type.pk, "fichier": "reference-test", "date_depot": "2026-10-23",
            "date_expiration": "2027-10-23", "employes": [self.owner.pk, self.other.pk],
        }, format="json")
        self.assertEqual(created.status_code, 201, created.data)
        self.assertEqual(set(created.data["employes"]), {self.owner.pk, self.other.pk})
        detail = self.client.get(reverse("document-detail", args=[created.data["id"]]))
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data["type_document_libelle"], self.type.libelle)
        deleted = self.client.delete(reverse("document-detail", args=[created.data["id"]]))
        self.assertEqual(deleted.status_code, 204)
        self.assertFalse(Document.objects.filter(pk=created.data["id"]).exists())

    def test_invalid_expiration_is_rejected(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.post(reverse("document-list"), {
            "type_document": self.type.pk, "fichier": "test", "date_depot": "2026-10-23",
            "date_expiration": "2026-10-22", "employes": [self.owner.pk],
        }, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("date_expiration", response.data)

    def test_type_codes_are_automatic_and_used_types_cannot_be_deleted(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.post(reverse("type-document-list"), {"libelle": "Attestation", "is_active": True}, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertTrue(response.data["code"].startswith("DOC_"))
        blocked = self.client.delete(reverse("type-document-detail", args=[self.type.pk]))
        self.assertEqual(blocked.status_code, 400)
        self.assertTrue(Document.objects.filter(pk=self.own_document.pk).exists())

    def test_permissions_combine_across_roles(self):
        additional = Role.objects.create(nom="M3_EXTRA_MANAGE")
        additional.permissions.add(get_permission_by_code("document.manage"))
        self.owner.roles.add(additional)
        response = self.client.get(reverse("document-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual({row["id"] for row in response.data}, {self.own_document.pk, self.other_document.pk})

    def test_inactive_type_cannot_be_used_for_new_reference(self):
        self.client.force_authenticate(user=self.manager)
        self.type.is_active = False
        self.type.save(update_fields=["is_active"])
        response = self.client.post(reverse("document-list"), {
            "type_document": self.type.pk, "fichier": "new-reference", "date_depot": "2026-10-23",
            "employes": [self.owner.pk],
        }, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("type_document", response.data)
        self.assertFalse(Document.objects.filter(fichier="new-reference").exists())
