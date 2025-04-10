from django.apps import AppConfig

class RegisterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'register'

    def ready(self):
        # Importing but won't get called create_initial_admin here
        # will be handled this  after migrations
        import os
        # Only run when the server is run directly
        if os.environ.get('RUN_MAIN', None) == 'true':
            # This conditional prevents the code from running during migrations
            pass