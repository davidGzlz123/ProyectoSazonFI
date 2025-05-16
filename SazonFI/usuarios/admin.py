from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario  # Importa Usuario desde .models

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('rol',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('rol',)}),
    )