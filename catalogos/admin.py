from django.contrib import admin

from .models import Estado, OOAD, Region, UMAE, UnidadMedica


admin.site.register(Region)
admin.site.register(Estado)
admin.site.register(OOAD)
admin.site.register(UMAE)
admin.site.register(UnidadMedica)