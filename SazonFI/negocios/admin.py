from django.contrib import admin
from .models import Negocio  # Importa Negocio desde .models

@admin.register(Negocio)
class NegocioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'usuario', 'direccion']
    search_fields = ['nombre', 'direccion']