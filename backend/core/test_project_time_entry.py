from django.urls import reverse
from rest_framework.test import APITestCase

from core.models import AffectationProjet, Contrat, Employe, Projet, Role, TacheProjet, FeuilleTemps, LigneFeuilleTemps
from core.permission_codes import get_permission_by_code
from core.services.projet_service import projet_service


class ProjectTimeEntryTests(APITestCase):
    def setUp(self):
        self.manager = self.employee("MANAGER")
        self.worker = self.employee("WORKER")
        self.manager.roles.add(Role.objects.get(nom="FRONTEND_MODULE_7_FEUILLES_TEMPS"))
        self.worker.roles.add(Role.objects.get(nom="EMPLOYE_SIMPLE"))
        Contrat.objects.create(employe=self.worker, date_debut="2026-01-01", salaire_base="220000", heures_journalieres="8")
        self.client.force_authenticate(self.manager)

    @staticmethod
    def employee(suffix):
        return Employe.objects.create_user(email=f"project-options-{suffix}@example.com", password=None,
            nom="Test", prenom=suffix, matricule=f"PO-{suffix}", num_secu_sociale=f"PO-SSN-{suffix}",
            date_naissance="1990-01-01", date_entree="2020-01-01", adresse="Test", telephone="0000")

    def create_project(self, name="Projet de test", **extra):
        response = self.client.post(reverse("projet-list"), {"nom": name, **extra}, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        return response.data

    def create_task(self, project_id, name="Analyse", **extra):
        response = self.client.post(reverse("projet-tache-list", args=[project_id]), {"nom": name, **extra}, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        return response.data

    def test_project_code_is_generated_without_input_and_client_cannot_choose_it(self):
        first = self.create_project()
        second = self.create_project("Autre projet", code="CODE-IMPOSE")
        for project in (first, second):
            self.assertRegex(project["code"], r"^PROJ_[A-F0-9]{24}$")
            self.assertLessEqual(len(project["code"]), 30)
        self.assertNotEqual(first["code"], second["code"])
        self.assertNotEqual(second["code"], "CODE-IMPOSE")

    def test_task_codes_are_generated_and_duplicate_names_are_still_rejected(self):
        project = self.create_project()
        first = self.create_task(project["id"])
        second = self.create_task(project["id"], "Développement", code="CODE-IMPOSE")
        self.assertRegex(first["code"], r"^TASK_[A-F0-9]{24}$")
        self.assertNotEqual(first["code"], second["code"])
        duplicate = self.client.post(reverse("projet-tache-list", args=[project["id"]]), {"nom": "Analyse"}, format="json")
        self.assertEqual(duplicate.status_code, 400)
        self.assertIn("nom", duplicate.data)

    def test_existing_codes_are_preserved_on_updates(self):
        project = Projet.objects.create(code="ANCIEN-PROJET", nom="Ancien projet")
        task = TacheProjet.objects.create(projet=project, code="ANCIENNE-TACHE", nom="Ancienne tâche")
        edit_role = Role.objects.create(nom="PROJECT_TEST_EDIT")
        edit_role.permissions.add(get_permission_by_code("projet.update"), get_permission_by_code("tache.update"))
        self.manager.roles.add(edit_role)
        response = self.client.put(reverse("projet-detail", args=[project.pk]), {"nom": "Nouveau nom", "code": "REMPLACER"}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["code"], "ANCIEN-PROJET")
        response = self.client.put(reverse("projet-tache-detail", args=[project.pk, task.pk]), {"nom": "Tâche renommée", "code": "REMPLACER"}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["code"], "ANCIENNE-TACHE")
        self.assertEqual(projet_service.update_project(project.pk, {"code": "INTERNE"}).code, "ANCIEN-PROJET")
        self.assertEqual(projet_service.update_task(task.pk, {"code": "INTERNE"}).code, "ANCIENNE-TACHE")

    def test_assigned_options_see_new_tasks_and_exclude_unassigned_or_inactive_records(self):
        project = self.create_project()
        unrelated = self.create_project("Autre projet")
        self.create_task(unrelated["id"], "Confidentielle")
        self.client.force_authenticate(self.worker)
        endpoint = reverse("feuille-temps-projets")
        self.assertEqual(self.client.get(endpoint).data, [])
        self.client.force_authenticate(self.manager)
        first = self.create_task(project["id"])
        self.assertEqual(self.client.post(reverse("projet-affectation-list", args=[project["id"]]), {"employe": self.worker.pk}, format="json").status_code, 201)
        self.client.force_authenticate(self.worker)
        response = self.client.get(endpoint)
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual([row["id"] for row in response.data], [project["id"]])
        self.assertEqual([row["id"] for row in response.data[0]["taches"]], [first["id"]])
        self.client.force_authenticate(self.manager)
        second = self.create_task(project["id"], "Nouvelle tâche")
        self.create_task(project["id"], "Inactive", actif=False)
        self.client.force_authenticate(self.worker)
        options = self.client.get(endpoint).data
        self.assertEqual({row["id"] for row in options[0]["taches"]}, {first["id"], second["id"]})
        Projet.objects.filter(pk=project["id"]).update(actif=False)
        self.assertEqual(self.client.get(endpoint).data, [])

    def test_simple_employee_can_save_newly_assigned_task_and_submit(self):
        project = self.create_project()
        task = self.create_task(project["id"])
        AffectationProjet.objects.create(projet_id=project["id"], employe=self.worker)
        self.client.force_authenticate(self.worker)
        response = self.client.post(reverse("feuille-temps-list"), {
            "semaine_debut": "2026-10-19", "lignes": [{"date_travail": "2026-10-20", "projet": project["id"], "tache": task["id"], "heures": "4"}],
        }, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["lignes"][0]["tache"], task["id"])
        self.assertEqual(response.data["total_heures"], "4.00")
        self.assertEqual(self.client.post(reverse("feuille-temps-soumettre", args=[response.data["id"]])).status_code, 200)

    def test_employee_cannot_grant_self_project_access(self):
        project = self.create_project()
        self.client.force_authenticate(self.worker)
        self.assertEqual(self.client.post(reverse("projet-list"), {"nom": "Non autorisé"}, format="json").status_code, 403)
        self.assertEqual(self.client.post(reverse("projet-affectation-list", args=[project["id"]]), {"employe": self.worker.pk}, format="json").status_code, 403)

    def test_manager_can_delete_unused_task_and_employee_sees_updated_options(self):
        project = self.create_project()
        task = self.create_task(project["id"])
        AffectationProjet.objects.create(projet_id=project["id"], employe=self.worker)
        endpoint = reverse("projet-tache-detail", args=[project["id"], task["id"]])
        self.client.force_authenticate(self.worker)
        self.assertEqual(self.client.delete(endpoint).status_code, 403)
        self.assertEqual(len(self.client.get(reverse("feuille-temps-projets")).data[0]["taches"]), 1)
        self.client.force_authenticate(self.manager)
        self.assertEqual(self.client.delete(endpoint).status_code, 204)
        self.assertFalse(TacheProjet.objects.filter(pk=task["id"]).exists())
        self.client.force_authenticate(self.worker)
        self.assertEqual(self.client.get(reverse("feuille-temps-projets")).data[0]["taches"], [])

    def test_task_used_by_timesheet_cannot_be_deleted_and_returns_readable_error(self):
        project = self.create_project()
        task = self.create_task(project["id"])
        sheet = FeuilleTemps.objects.create(employe=self.worker, semaine_debut="2026-10-19")
        line = LigneFeuilleTemps.objects.create(feuille=sheet, projet_id=project["id"], tache_id=task["id"],
            date_travail="2026-10-20", heures="2")
        response = self.client.delete(reverse("projet-tache-detail", args=[project["id"], task["id"]]))
        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("feuille de temps", str(response.data))
        self.assertTrue(LigneFeuilleTemps.objects.filter(pk=line.pk).exists())
        self.assertTrue(TacheProjet.objects.filter(pk=task["id"]).exists())

    def test_pending_tasks_follow_validation_without_hiding_history_or_other_employees_tasks(self):
        project = self.create_project()
        first = self.create_task(project["id"], "Première tâche")
        second = self.create_task(project["id"], "Deuxième tâche")
        for employee in (self.worker, self.manager):
            AffectationProjet.objects.create(projet_id=project["id"], employe=employee)
        sheet = FeuilleTemps.objects.create(employe=self.worker, semaine_debut="2026-10-19")
        LigneFeuilleTemps.objects.create(feuille=sheet, projet_id=project["id"], tache_id=first["id"],
            date_travail="2026-10-20", heures="2")
        endpoint = reverse("feuille-temps-projets")
        self.client.force_authenticate(self.worker)

        def pending_ids():
            response = self.client.get(endpoint, {"a_saisir": "true"})
            self.assertEqual(response.status_code, 200, response.data)
            return {task["id"] for project in response.data for task in project["taches"]}

        for status in ("BROUILLON", "SOUMISE"):
            sheet.statut = status
            sheet.save()
            self.assertEqual(pending_ids(), {first["id"], second["id"]})
        sheet.statut = "VALIDEE"
        sheet.save()
        self.assertEqual(pending_ids(), {second["id"]})
        self.assertEqual(len(self.client.get(endpoint).data[0]["taches"]), 2)
        self.assertEqual(self.client.get(reverse("feuille-temps-list")).data[0]["id"], sheet.pk)
        self.client.force_authenticate(self.manager)
        self.assertEqual(pending_ids(), {first["id"], second["id"]})
        self.client.force_authenticate(self.worker)
        LigneFeuilleTemps.objects.create(feuille=sheet, projet_id=project["id"], tache_id=second["id"],
            date_travail="2026-10-20", heures="2")
        self.assertEqual(self.client.get(endpoint, {"a_saisir": "true"}).data, [])
        sheet.statut = "BROUILLON"
        sheet.save()
        self.assertEqual(pending_ids(), {first["id"], second["id"]})
