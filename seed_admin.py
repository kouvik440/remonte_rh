import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'remonte_rh.settings')
import django
django.setup()

from core.models import Departement, Permission, Role, Employe

# Department
department, _ = Departement.objects.get_or_create(nom='Direction RH', code='RH')

# Role
role, _ = Role.objects.get_or_create(
    nom='ADMIN_RH',
    defaults={'description': 'Administrateur RH'}
)
role.permissions.set(Permission.objects.filter(code__in=[
    'employe.read',
    'employe.create',
    'employe.update',
    'employe.delete',
]))

employee, _ = Employe.objects.get_or_create(
    matricule='RH-001',
    defaults={
        'email': 'admin.rh@example.com',
        'nom': 'Dupont',
        'prenom': 'Alice',
        'date_naissance': '1990-01-15',
        'adresse': '1 Rue de Paris',
        'telephone': '0612345678',
        'num_secu_sociale': '123456789',
        'date_entree': '2020-09-01',
        'statut': 'ACTIF',
        'is_active': True,
        'is_staff': True,
        'department': department,
    }
)
employee.email = 'admin.rh@example.com'
employee.set_password('SecurePassword123!')
employee.is_staff = True
employee.roles.set([role])
employee.save()

print('employee=', employee.email)
print('password=', 'SecurePassword123!')
print('role=', role.nom)
print('employee_id=', employee.pk)
