from django.db import migrations


# Frozen profile definitions: personal timesheets already use authentication and
# ownership checks, rather than the generic feuille_temps CRUD permissions.
PROFILES = {
    "EMPLOYE_SIMPLE": {
        "description": "Accès personnel : demandes et soldes de congés, coordonnées bancaires et feuilles de temps. Aucun accès de gestion ni aux paies globales.",
        "permissions": (
            ("typeconge", "view_typeconge"),
            ("demandeabsence", "view_demandeabsence"),
            ("demandeabsence", "add_demandeabsence"),
            ("soldeconge", "view_soldeconge"),
            ("coordonneesbancaires", "view_coordonneesbancaires"),
            ("coordonneesbancaires", "add_coordonneesbancaires"),
            ("coordonneesbancaires", "change_coordonneesbancaires"),
        ),
    },
    "FRONTEND_MODULE_6_TGM": {
        "description": "Consultation des taux et coûts projets, simulation de marge. paie.read donne aussi accès aux paies globales et à la masse salariale.",
        "permissions": (("paie", "view_paie"),),
    },
    "FRONTEND_MODULE_7_FEUILLES_TEMPS": {
        "description": "Gestionnaire des temps : décisions, création de projets/tâches et affectation des employés. Ajouter le profil TGM pour consulter les coûts.",
        "permissions": (
            ("feuilletemps", "decide"),
            ("projet", "view_projet"),
            ("projet", "add_projet"),
            ("projet", "assign_employees"),
            ("tacheprojet", "view_tacheprojet"),
            ("tacheprojet", "add_tacheprojet"),
            ("employe", "view_employe"),
        ),
    },
}


def create_profiles(apps, schema_editor):
    database = schema_editor.connection.alias
    roles = apps.get_model("core", "Role")
    permissions = apps.get_model("auth", "Permission")
    content_types = apps.get_model("contenttypes", "ContentType")
    for name, profile in PROFILES.items():
        role, _ = roles.objects.using(database).get_or_create(nom=name, defaults={"description": profile["description"]})
        for model, codename in profile["permissions"]:
            content_type, _ = content_types.objects.using(database).get_or_create(app_label="core", model=model)
            permission, _ = permissions.objects.using(database).get_or_create(content_type_id=content_type.pk, codename=codename,
                defaults={"name": f"Can {codename.replace('_', ' ')}"})
            roles.permissions.through.objects.using(database).get_or_create(role_id=role.pk, permission_id=permission.pk)


class Migration(migrations.Migration):
    dependencies = [("core", "0043_department_management_permissions")]
    operations = [migrations.RunPython(create_profiles, migrations.RunPython.noop)]
