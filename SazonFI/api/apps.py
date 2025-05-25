from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        # Importar las señales aquí para asegurarte de que se registren al iniciar la app
        import api.signals
