from django.apps import AppConfig


class PayappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payapp'

    def ready(self):
        import os
        # Only run when the server starts, not during migrations
        if os.environ.get('RUN_MAIN') != 'true':
            # Start the Thrift server
            from thrift_server import start_thrift_server
            start_thrift_server()