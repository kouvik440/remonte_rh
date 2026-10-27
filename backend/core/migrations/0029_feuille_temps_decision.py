from django.db import migrations, models
import django.db.models.deletion


def create_timesheet_decision_permission(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    Permission = apps.get_model("auth", "Permission")
    Role = apps.get_model("core", "Role")
    database = schema_editor.connection.alias

    content_type, _ = ContentType.objects.using(database).get_or_create(
        app_label="core",
        model="feuilletemps",
    )
    permission, _ = Permission.objects.using(database).get_or_create(
        content_type_id=content_type.pk,
        codename="decide",
        defaults={"name": "Can decide submitted timesheets"},
    )
    admin_role = Role.objects.using(database).filter(nom__iexact="ADMIN_RH").first()
    if admin_role is not None:
        Role.permissions.through.objects.using(database).get_or_create(
            role_id=admin_role.pk,
            permission_id=permission.pk,
        )


def remove_timesheet_decision_permission(apps, schema_editor):
    Permission = apps.get_model("auth", "Permission")
    database = schema_editor.connection.alias
    Permission.objects.using(database).filter(
        content_type__app_label="core",
        content_type__model="feuilletemps",
        codename="decide",
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0028_feuille_temps_and_contrat_hours"),
    ]

    operations = [
        migrations.AddField(
            model_name="feuilletemps",
            name="date_decision",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="feuilletemps",
            name="motif_refus",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="feuilletemps",
            name="valideur",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="feuilles_temps_validees",
                to="core.employe",
            ),
        ),
        migrations.AlterModelOptions(
            name="feuilletemps",
            options={
                "ordering": ["-semaine_debut", "employe__nom", "employe__prenom"],
                "permissions": [
                    ("decide", "Can decide submitted timesheets"),
                ],
            },
        ),
        migrations.RunPython(
            create_timesheet_decision_permission,
            remove_timesheet_decision_permission,
        ),
    ]
