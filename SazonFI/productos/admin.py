from django.contrib import admin
from .models import Producto  # Importa Producto desde .models

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'negocio', 'precio', 'stock']
    list_filter = ['negocio']
    search_fields = ['nombre', 'descripcion']