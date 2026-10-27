from datetime import timedelta

from core.services.demande_absence_service import demande_absence_service
from core.services.employe_service import employe_service


class PlanningService:
    def __init__(self, employe_service, demande_absence_service):
        self.employe_service = employe_service
        self.demande_absence_service = demande_absence_service

    def get_events(
        self,
        date_debut,
        date_fin,
        department_id=None,
        employee_id=None,
    ) -> list:
        absences = self.demande_absence_service.calendar(
            date_debut,
            date_fin,
            department_id=department_id,
            employee_id=employee_id,
        )
        employes = self.employe_service.get_for_calendar(
            date_debut,
            date_fin,
            department_id=department_id,
            employee_id=employee_id,
        )

        events = [self._absence_event(absence) for absence in absences]
        absence_dates = {}
        for absence in absences:
            current_date = max(absence.date_debut, date_debut)
            last_date = min(absence.date_fin, date_fin)
            while current_date <= last_date:
                absence_dates.setdefault(absence.employe_id, set()).add(current_date)
                current_date += timedelta(days=1)

        for employe in employes:
            current_date = max(date_debut, employe.date_entree)
            last_date = min(
                date_fin,
                employe.date_sortie or date_fin,
            )
            while current_date <= last_date:
                if (
                    current_date.weekday() < 5
                    and current_date not in absence_dates.get(employe.pk, set())
                ):
                    events.append(self._presence_event(employe, current_date))
                current_date += timedelta(days=1)

        return sorted(
            events,
            key=lambda event: (
                event["date_debut"],
                event["employe_nom"],
                event["employe_prenom"],
                event["type_evenement"],
            ),
        )

    @staticmethod
    def _absence_event(absence):
        employe = absence.employe
        departement = employe.department
        return {
            "id": f"absence-{absence.pk}",
            "type_evenement": "ABSENCE",
            "demande_absence_id": absence.pk,
            "employe_id": employe.pk,
            "employe_nom": employe.nom,
            "employe_prenom": employe.prenom,
            "departement_id": employe.department_id,
            "departement_nom": departement.nom if departement else None,
            "type_conge_code": absence.type_conge.code,
            "type_conge_libelle": absence.type_conge.libelle,
            "date_debut": absence.date_debut,
            "date_fin": absence.date_fin,
        }

    @staticmethod
    def _presence_event(employe, jour):
        departement = employe.department
        return {
            "id": f"presence-{employe.pk}-{jour.isoformat()}",
            "type_evenement": "PRESENCE_PREVUE",
            "demande_absence_id": None,
            "employe_id": employe.pk,
            "employe_nom": employe.nom,
            "employe_prenom": employe.prenom,
            "departement_id": employe.department_id,
            "departement_nom": departement.nom if departement else None,
            "type_conge_code": None,
            "type_conge_libelle": None,
            "date_debut": jour,
            "date_fin": jour,
        }


planning_service = PlanningService(employe_service, demande_absence_service)
