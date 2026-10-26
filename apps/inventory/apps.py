from django.apps import AppConfig


class InventoryConfig(AppConfig):
    name = "apps.inventory"

    def ready(self):
        from . import signals  # noqa: F401
