from django.apps import AppConfig

class PmsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pms'

    # --- ADD THIS METHOD ---
    # This imports our signals file when the app is ready
    def ready(self):
        import pms.signals