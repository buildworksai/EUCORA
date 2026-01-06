# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Management command to create default development user for authentication.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import IntegrityError


class Command(BaseCommand):
    help = 'Create default development user for testing'

    def handle(self, *args, **options):
        try:
            # Create default dev user
            user, created = User.objects.get_or_create(
                username='devadmin',
                defaults={
                    'email': 'admin@eucora.local',
                    'first_name': 'Dev',
                    'last_name': 'Admin',
                    'is_staff': True,
                    'is_superuser': True,
                }
            )
            
            if created:
                user.set_password('eucora-dev-password')
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created default development user:\n'
                        f'  Username: devadmin\n'
                        f'  Email: admin@eucora.local\n'
                        f'  Password: eucora-dev-password'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'User "devadmin" already exists (email: {user.email})'
                    )
                )
                
        except IntegrityError as e:
            self.stdout.write(self.style.ERROR(f'Error creating user: {e}'))
