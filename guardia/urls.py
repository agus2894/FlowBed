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
    
    # API para actualizar el estado de una posición
    path('api/posiciones/<str:posicion_id>/estado/', views.actualizar_estado, name='actualizar_estado'),
    
    # API para marcar el destino final asignado
    path('api/posiciones/<str:posicion_id>/marcar-destino/', views.marcar_destino_asignado, name='marcar_destino_asignado'),
]
