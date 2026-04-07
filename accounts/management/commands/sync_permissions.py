"""
Management commands for permission synchronization and maintenance.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.permission_bulk import BulkPermissionManager, PermissionAnalytics
from accounts.permission_sync import PermissionSyncManager
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Synchronize all permissions in the system'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force synchronization of all permissions',
        )
        parser.add_argument(
            '--analytics',
            action='store_true',
            help='Show permission analytics',
        )
        parser.add_argument(
            '--check-conflicts',
            action='store_true',
            help='Check for permission conflicts',
        )
    
    def handle(self, *args, **options):
        """Handle the command execution."""
        self.stdout.write(self.style.SUCCESS('Starting permission synchronization...'))
        
        try:
            if options['analytics']:
                self.show_analytics()
            
            if options['check_conflicts']:
                self.check_conflicts()
            
            if options['force'] or not (options['analytics'] or options['check_conflicts']):
                self.synchronize_permissions()
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during synchronization: {e}')
            )
            logger.error(f"Permission sync command error: {e}")
    
    def synchronize_permissions(self):
        """Perform full permission synchronization."""
        try:
            BulkPermissionManager.bulk_sync_all_permissions()
            self.stdout.write(
                self.style.SUCCESS('✓ All permissions synchronized successfully')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Synchronization failed: {e}')
            )
            raise
    
    def show_analytics(self):
        """Display permission analytics."""
        try:
            stats = PermissionAnalytics.get_permission_statistics()
            
            self.stdout.write('\n' + self.style.SUCCESS('=== Permission Analytics ==='))
            self.stdout.write(f"Total Users: {stats['total_users']}")
            self.stdout.write(f"Custom Users: {stats['custom_users']}")
            self.stdout.write(f"Role-based Users: {stats['role_based_users']}")
            self.stdout.write(f"Total Roles: {stats['total_roles']}")
            self.stdout.write(f"Total Permissions: {stats['total_permissions']}")
            self.stdout.write(f"Role Permissions: {stats['role_permissions']}")
            self.stdout.write(f"User Permissions: {stats['user_permissions']}")
            
            if stats['permission_categories']:
                self.stdout.write('\nPermission Categories:')
                for category, count in stats['permission_categories'].items():
                    self.stdout.write(f"  {category}: {count}")
            
            if stats['role_distribution']:
                self.stdout.write('\nRole Distribution:')
                for role, count in stats['role_distribution'].items():
                    self.stdout.write(f"  {role}: {count}")
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Analytics generation failed: {e}')
            )
    
    def check_conflicts(self):
        """Check for permission conflicts."""
        try:
            conflicts = PermissionAnalytics.identify_permission_conflicts()
            
            if not conflicts:
                self.stdout.write(
                    self.style.SUCCESS('✓ No permission conflicts found')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('⚠ Permission conflicts detected:')
                )
                for conflict in conflicts:
                    self.stdout.write(f"  Type: {conflict['type']}")
                    self.stdout.write(f"  Message: {conflict['message']}")
                    if 'users' in conflict:
                        self.stdout.write(f"  Users: {', '.join(conflict['users'])}")
                    if 'roles' in conflict:
                        self.stdout.write(f"  Roles: {', '.join(conflict['roles'])}")
                    self.stdout.write('')
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Conflict detection failed: {e}')
            )
