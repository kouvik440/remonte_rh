from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import Group, Permission as AuthPermission, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models

from core.permission_codes import permission_identity

from .enums import StatutEmploye


class EmployeManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'email est requis.")

        employee = self.model(email=self.normalize_email(email), **extra_fields)
        if password:
            employee.set_password(password)
        else:
            employee.set_unusable_password()
        employee.save(using=self._db)
        return employee

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Un superutilisateur doit avoir is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Un superutilisateur doit avoir is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


class Employe(AbstractBaseUser, PermissionsMixin, models.Model):
    matricule = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128, default="!", editable=False)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField()
    adresse = models.TextField()
    telephone = models.CharField(max_length=30)
    num_secu_sociale = models.CharField(max_length=50, unique=True)
    date_entree = models.DateField()
    date_sortie = models.DateField(null=True, blank=True)
    statut = models.CharField(
        max_length=20,
        choices=StatutEmploye.choices,
        default=StatutEmploye.ACTIF,
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    department = models.ForeignKey(
        "core.Departement",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employes",
    )
    responsable = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="collaborateurs",
    )

    roles = models.ManyToManyField(
        "core.Role",
        related_name="employes",
        blank=True,
    )
    groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name="employes",
        related_query_name="employe",
    )
    user_permissions = models.ManyToManyField(
        AuthPermission,
        blank=True,
        related_name="employes",
        related_query_name="employe",
    )

    objects = EmployeManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = [
        "matricule",
        "nom",
        "prenom",
        "date_naissance",
        "adresse",
        "telephone",
        "num_secu_sociale",
        "date_entree",
    ]

    class Meta:
        ordering = ["nom", "prenom"]

    def clean(self):
        super().clean()
        if self.date_sortie and self.date_sortie < self.date_entree:
            raise ValidationError(
                {"date_sortie": "La date de sortie doit être après la date d'entrée."}
            )

    def has_role(self, role_name: str) -> bool:
        return self.roles.filter(nom__iexact=role_name).exists()

    def has_permission(self, permission_code: str) -> bool:
        model_name, codename = permission_identity(permission_code)
        return self.roles.filter(
            permissions__content_type__app_label="core",
            permissions__content_type__model=model_name,
            permissions__codename=codename,
        ).exists()

    def __str__(self):
        return f"{self.prenom} {self.nom}"

    def get_full_name(self):
        return f"{self.prenom} {self.nom}"

    def get_short_name(self):
        return self.nom

