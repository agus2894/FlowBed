from django.contrib import admin
from .models import Posicion, EventoEgreso


@admin.register(Posicion)
class PosicionAdmin(admin.ModelAdmin):
    """Administración de posiciones hospitalarias"""
    list_display = ['id', 'tipo', 'estado', 'nombre_paciente', 'timestamp_estado']
    list_filter = ['tipo', 'estado']
    search_fields = ['id', 'nombre_paciente']
    ordering = ['id']


@admin.register(EventoEgreso)
class EventoEgresoAdmin(admin.ModelAdmin):
    """Administración de eventos de egreso"""
    list_display = ['paciente', 'posicion_id', 'destino', 'timestamp_ingreso', 'timestamp_egreso', 'duracion']
    list_filter = ['destino', 'timestamp_egreso']
    search_fields = ['paciente', 'posicion_id']
    ordering = ['-timestamp_egreso']
    readonly_fields = ['duracion']
