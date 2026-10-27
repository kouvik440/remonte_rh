from core.models import EmployeHistorique


def record_change(employee_id, category, object_id, before, after, actor=None, initial=False):
    if before == after:
        return
    EmployeHistorique.objects.create(employe_id=employee_id, categorie=category, objet_id=object_id,
        operation="INITIAL" if initial else "CREATION" if not before else "SUPPRESSION" if not after else "MODIFICATION",
        avant=before, apres=after, auteur=actor, auteur_nom=actor.get_full_name() if actor else "")


def contract_snapshot(contract):
    return {"date_debut": str(contract.date_debut), "date_fin": str(contract.date_fin) if contract.date_fin else None,
        "salaire_base": str(contract.salaire_base), "heures_journalieres": str(contract.heures_journalieres) if contract.heures_journalieres is not None else None,
        "statut": contract.statut, "poste": position_snapshot(contract.poste) if contract.poste_id else {},
        "types_contrat": [{"id": item.pk, "libelle": item.type} for item in contract.type.order_by("pk")]}


def position_snapshot(position):
    return {"nom": position.nom, "description": position.description}


def manager_snapshot(employee):
    return {"id": employee.responsable_id, "nom": employee.responsable.get_full_name()} if employee.responsable_id else {}
