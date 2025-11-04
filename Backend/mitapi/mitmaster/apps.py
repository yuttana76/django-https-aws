from django.apps import AppConfig


class MitmasterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mitmaster'

    def ready(self):
        from .mit_scheduler import mit_sch
        mit_sch.start()
