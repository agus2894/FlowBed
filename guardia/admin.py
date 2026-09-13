from django.contrib import admin
from .models import Posicion, EventoEgreso


@admin.register(Posicion)
class PosicionAdmin(admin.ModelAdmin):
    """Administración de posiciones hospitalarias"""
    list_display = ['id', 'tipo', 'estado', 'etapa_circuito', 'nombre_paciente', 'destino_solicitado', 'destino_asignado', 'cama_asignada_detalle', 'timestamp_estado']
    list_filter = ['tipo', 'estado', 'etapa_circuito', 'destino_solicitado', 'destino_asignado']
    search_fields = ['id', 'nombre_paciente', 'cama_asignada_detalle']
    ordering = ['id']


@admin.register(EventoEgreso)
class EventoEgresoAdmin(admin.ModelAdmin):
    """Administración de eventos de egreso y traslados"""
    list_display = ['paciente', 'posicion_id', 'destino', 'cama_asignada_detalle', 'duracion_espera_cama', 'duracion_total_guardia', 'timestamp_egreso']
    list_filter = ['destino', 'timestamp_egreso']
    search_fields = ['paciente', 'posicion_id', 'cama_asignada_detalle']
    ordering = ['-timestamp_egreso']
    readonly_fields = ['duracion', 'duracion_espera_cama', 'duracion_total_guardia']

