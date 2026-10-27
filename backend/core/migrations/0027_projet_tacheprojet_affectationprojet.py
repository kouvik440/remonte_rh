from django.db import migrations, models
import django.db.models.deletion


def create_project_permissions(apps, schema_editor):
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    Role = apps.get_model("core", "Role")
    database = schema_editor.connection.alias
    permissions = (
        ("projet", "add_projet", "Can add project"),
        ("projet", "change_projet", "Can change project"),
        ("projet", "delete_projet", "Can delete project"),
        ("projet", "view_projet", "Can view project"),
        ("projet", "assign_employees", "Can assign employees to project"),
        ("tacheprojet", "add_tacheprojet", "Can add project task"),
        ("tacheprojet", "change_tacheprojet", "Can change project task"),
        ("tacheprojet", "delete_tacheprojet", "Can delete project task"),
        ("tacheprojet", "view_tacheprojet", "Can view project task"),
    )
    admin_role = Role.objects.using(database).filter(nom__iexact="ADMIN_RH").first()
    role_permissions = Role.permissions.through
    for model_name, codename, name in permissions:
        content_type, _ = ContentType.objects.using(database).get_or_create(
            app_label="core",
            model=model_name,
        )
        permission, _ = Permission.objects.using(database).get_or_create(
            content_type_id=content_type.pk,
            codename=codename,
            defaults={"name": name},
        )
        if admin_role is not None:
            role_permissions.objects.using(database).get_or_create(
                role_id=admin_role.pk,
                permission_id=permission.pk,
            )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0026_paie_bulletin_pdf"),
    ]

    operations = [
        migrations.CreateModel(
            name="Projet",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("code", models.CharField(max_length=30, unique=True)),
                ("nom", models.CharField(max_length=150)),
                ("description", models.TextField(blank=True)),
                ("date_debut", models.DateField(blank=True, null=True)),
                ("date_fin", models.DateField(blank=True, null=True)),
                ("actif", models.BooleanField(default=True)),
            ],
            options={
                "ordering": ["nom"],
                "permissions": [
                    ("assign_employees", "Can assign employees to project"),
                ],
            },
        ),
        migrations.CreateModel(
            name="TacheProjet",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("code", models.CharField(max_length=30)),
                ("nom", models.CharField(max_length=150)),
                ("description", models.TextField(blank=True)),
                ("actif", models.BooleanField(default=True)),
                (
                    "projet",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="taches",
                        to="core.projet",
                    ),
                ),
            ],
            options={
                "ordering": ["projet__nom", "nom"],
            },
        ),
        migrations.CreateModel(
            name="AffectationProjet",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date_affectation", models.DateTimeField(auto_now_add=True)),
                (
                    "employe",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="affectations_projet",
                        to="core.employe",
                    ),
                ),
                (
                    "projet",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="affectations",
                        to="core.projet",
                    ),
                ),
            ],
            options={
                "ordering": ["employe__nom", "employe__prenom"],
            },
        ),
        migrations.AddConstraint(
            model_name="tacheprojet",
            constraint=models.UniqueConstraint(
                fields=("projet", "code"),
                name="unique_tache_projet_code",
            ),
        ),
        migrations.AddConstraint(
            model_name="tacheprojet",
            constraint=models.UniqueConstraint(
                fields=("projet", "nom"),
                name="unique_tache_projet_nom",
            ),
        ),
        migrations.AddConstraint(
            model_name="affectationprojet",
            constraint=models.UniqueConstraint(
                fields=("projet", "employe"),
                name="uniq_proj_emp_assign",
            ),
        ),
        migrations.RunPython(
            create_project_permissions,
            migrations.RunPython.noop,
        ),
    ]
