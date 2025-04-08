from django.apps import AppConfig

class RegisterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'register'

    def ready(self):
        # Import but don't call create_initial_admin here
        # We'll handle this separately after migrations
        import os
        # Only run when the server is run directly (not during migrations)
        if os.environ.get('RUN_MAIN', None) == 'true':
            # This conditional prevents the code from running during migrations
            pass