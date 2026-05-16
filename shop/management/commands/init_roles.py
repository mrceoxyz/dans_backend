from django.core.management.base import BaseCommand
from shop.models import Role

class Command(BaseCommand):
    help = 'Initialize default roles'
    
    def handle(self, *args, **kwargs):
        roles_data = [
            {'name': 'owner', 'display_name': 'Owner', 'description': 'Full access'},
            {'name': 'manager', 'display_name': 'Manager', 'description': 'Manage operations'},
            {'name': 'tailor', 'display_name': 'Tailor', 'description': 'Manage orders'},
            {'name': 'assistant', 'display_name': 'Assistant', 'description': 'Limited access'},
            {'name': 'viewer', 'display_name': 'Viewer', 'description': 'Read-only'},
        ]
        
        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={
                    'display_name': role_data['display_name'],
                    'description': role_data['description']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created role: {role.display_name}'))