"""
URLs para la app guardia.
"""
from django.urls import path
from . import views

app_name = 'guardia'

urlpatterns = [
    # Vista principal del dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Vista del historial con estadísticas
    path('historial/', views.historial, name='historial'),
    
    # API para obtener todas las posiciones
    path('api/posiciones/', views.obtener_posiciones, name='obtener_posiciones'),
    
    # API SSE para sincronización en tiempo real
    path('api/posiciones/stream/', views.stream_posiciones, name='stream_posiciones'),
    
    # API para actualizar el estado de una posición
    # API para actualizar el estado general de una posición
    path('api/posiciones/<str:posicion_id>/estado/', views.actualizar_estado, name='actualizar_estado'),
    
    # API para marcar el destino final asignado
    # API Circuito - Paso 1: Solicitar Cama
    path('api/posiciones/<str:posicion_id>/solicitar-cama/', views.solicitar_cama, name='solicitar_cama'),
    
    # API Circuito - Paso 2: Aceptar / Asignar Cama
    path('api/posiciones/<str:posicion_id>/aceptar-asignar/', views.aceptar_asignar_cama, name='aceptar_asignar_cama'),
    
    # API Circuito - Paso 3: Confirmar Traslado y Liberar Cama
    path('api/posiciones/<str:posicion_id>/trasladar-egresar/', views.trasladar_egresar_paciente, name='trasladar_egresar_paciente'),
    
    # API: Completar Limpieza -> Libre
    path('api/posiciones/<str:posicion_id>/limpieza-completada/', views.completar_limpieza, name='completar_limpieza'),
    
    # API compatibilidad: Marcar destino
    path('api/posiciones/<str:posicion_id>/marcar-destino/', views.marcar_destino_asignado, name='marcar_destino_asignado'),
]

