from django.db import migrations


def seed_history(apps, schema_editor):
    database = schema_editor.connection.alias
    History = apps.get_model("core", "EmployeHistorique")
    Position = apps.get_model("core", "Poste")
    Contract = apps.get_model("core", "Contrat")
    entries = []
    for position in Position.objects.using(database).all().iterator():
        entries.append(History(employe_id=position.employe_id, categorie="POSTE", objet_id=position.pk, operation="INITIAL",
            avant={}, apres={"nom": position.nom, "description": position.description}))
    for contract in Contract.objects.using(database).prefetch_related("type").all().iterator(chunk_size=500):
        entries.append(History(employe_id=contract.employe_id, categorie="CONTRAT", objet_id=contract.pk, operation="INITIAL", avant={},
            apres={"date_debut": str(contract.date_debut), "date_fin": str(contract.date_fin) if contract.date_fin else None,
                "salaire_base": str(contract.salaire_base), "heures_journalieres": str(contract.heures_journalieres) if contract.heures_journalieres is not None else None,
                "statut": contract.statut, "types_contrat": [{"id": item.pk, "libelle": item.type} for item in sorted(contract.type.all(), key=lambda item: item.pk)]}))
    History.objects.using(database).bulk_create(entries, batch_size=500)


class Migration(migrations.Migration):
    dependencies = [("core", "0046_employee_hierarchy_and_history")]
    operations = [migrations.RunPython(seed_history, migrations.RunPython.noop)]
