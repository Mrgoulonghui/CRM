from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules

from stark.service.sites import site


class StarkConfig(AppConfig):
    name = 'stark'

    def ready(self):
        autodiscover_modules('stark', register_to=site)
