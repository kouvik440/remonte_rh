from django.contrib import admin
from django import forms
from django.contrib.auth.models import Permission

from .models import Employe, Role


class EmployeAdminForm(forms.ModelForm):
    password = forms.CharField(
        label="Mot de passe",
        required=False,
        widget=forms.PasswordInput,
    )

    class Meta:
        model = Employe
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password"].required = self.instance._state.adding

    def save(self, commit=True):
        employee = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            employee.set_password(password)
        elif not employee.pk:
            employee.set_unusable_password()
        if commit:
            employee.save()
            self.save_m2m()
        return employee


@admin.register(Employe)
class EmployeAdmin(admin.ModelAdmin):
    form = EmployeAdminForm
    list_display = ("matricule", "nom", "prenom", "email", "statut", "is_staff")
    search_fields = ("matricule", "email", "nom", "prenom")
    list_filter = ("statut", "is_active")
    filter_horizontal = ("roles", "groups", "user_permissions")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("nom", "description")
    filter_horizontal = ("permissions",)


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("name", "codename", "content_type")
    search_fields = ("name", "codename")
    list_filter = ("content_type__app_label",)
