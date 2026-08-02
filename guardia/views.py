"""
Vistas para la gestión de la guardia hospitalaria.
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json

from .models import Posicion, EventoEgreso


def dashboard(request):
    """
    Vista principal que muestra el dashboard con todas las posiciones.
    """
    posiciones = Posicion.objects.all().order_by('id')
    return render(request, 'guardia/dashboard.html', {
        'posiciones': posiciones
    })


@require_http_methods(["GET"])
def obtener_posiciones(request):
    """
    API: Devuelve todas las posiciones en formato JSON.
    """
    posiciones = Posicion.objects.all().order_by('id')
    datos = []
    
    for pos in posiciones:
        datos.append({
            'id': pos.id,
            'tipo': pos.tipo,
            'estado': pos.estado,
            'nombre_paciente': pos.nombre_paciente,
            'timestamp_estado': pos.timestamp_estado.isoformat() if pos.timestamp_estado else None,
            'timestamp_ingreso': pos.timestamp_ingreso.isoformat() if pos.timestamp_ingreso else None,
            'destino_solicitado': pos.destino_solicitado,
            'destino_asignado': pos.destino_asignado,
            'timestamp_destino_asignado': pos.timestamp_destino_asignado.isoformat() if pos.timestamp_destino_asignado else None,
        })
    
    return JsonResponse({'posiciones': datos})


@csrf_exempt
@require_http_methods(["POST"])
def actualizar_estado(request, posicion_id):
    """
    API: Actualiza el estado de una posición.
    Espera JSON: {
        "estado": "LIBRE|OCUPADO|LIMPIEZA|RESERVADO|FUERA_SERVICIO", 
        "nombre_paciente": "opcional",
        "destino_solicitado": "PISO|UTI|UTIM" (solo si estado es OCUPADO)
    }
    """
    try:
        posicion = Posicion.objects.get(id=posicion_id)
        data = json.loads(request.body)
        
        estado_anterior = posicion.estado
        nombre_paciente_anterior = posicion.nombre_paciente
        timestamp_ingreso_anterior = posicion.timestamp_ingreso
        destino_anterior = posicion.destino_solicitado
        
        nuevo_estado = data.get('estado')
        nombre_paciente = data.get('nombre_paciente', '')
        destino_solicitado = data.get('destino_solicitado', '')
        
        # Validar que el estado sea válido
        estados_validos = [e[0] for e in Posicion.ESTADOS]
        if nuevo_estado not in estados_validos:
            return JsonResponse({'error': 'Estado inválido'}, status=400)
        
        # Si pasa a OCUPADO, debe tener nombre de paciente y destino
        if nuevo_estado == 'OCUPADO':
            if not nombre_paciente:
                return JsonResponse({'error': 'Debe proporcionar el nombre del paciente'}, status=400)
            if not destino_solicitado:
                return JsonResponse({'error': 'Debe seleccionar el destino del paciente'}, status=400)
            
            # Validar destino
            destinos_validos = [d[0] for d in Posicion.DESTINOS]
            if destino_solicitado not in destinos_validos:
                return JsonResponse({'error': 'Destino inválido'}, status=400)
        
        # Si estaba OCUPADO y cambia a otro estado, crear EventoEgreso (solo si no se creó ya al marcar destino)
        if estado_anterior == 'OCUPADO' and nuevo_estado != 'OCUPADO':
            if timestamp_ingreso_anterior and nombre_paciente_anterior and destino_anterior:
                # Solo crear si no hay destino asignado (ya que si lo hay, ya se creó el evento)
                if not posicion.destino_asignado:
                    # Crear evento de egreso
                    evento = EventoEgreso.objects.create(
                        posicion_id=posicion_id,
                        paciente=nombre_paciente_anterior,
                        destino=destino_anterior,
                        timestamp_ingreso=timestamp_ingreso_anterior,
                    )
        
        # Actualizar la posición
        posicion.estado = nuevo_estado
        
        if nuevo_estado == 'OCUPADO':
            posicion.nombre_paciente = nombre_paciente
            posicion.destino_solicitado = destino_solicitado
            posicion.timestamp_ingreso = timezone.now()
        else:
            # Al cambiar de OCUPADO a otro estado, limpiar todos los datos
            posicion.nombre_paciente = None
            posicion.destino_solicitado = None
            posicion.timestamp_ingreso = None
            posicion.destino_asignado = None
            posicion.timestamp_destino_asignado = None
        
        posicion.save()
        
        return JsonResponse({
            'success': True,
            'posicion': {
                'id': posicion.id,
                'estado': posicion.estado,
                'nombre_paciente': posicion.nombre_paciente,
                'timestamp_estado': posicion.timestamp_estado.isoformat(),
                'timestamp_ingreso': posicion.timestamp_ingreso.isoformat() if posicion.timestamp_ingreso else None,
                'destino_solicitado': posicion.destino_solicitado,
            }
        })
        
    except Posicion.DoesNotExist:
        return JsonResponse({'error': 'Posición no encontrada'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def marcar_destino_asignado(request, posicion_id):
    """
    API: Marca el destino final asignado y detiene el cronómetro.
    Espera JSON: {
        "destino_asignado": "PISO|UTI|UTIM"
    }
    """
    try:
        posicion = Posicion.objects.get(id=posicion_id)
        data = json.loads(request.body)
        
        # Validar que la posición esté ocupada
        if posicion.estado != 'OCUPADO':
            return JsonResponse({'error': 'La posición debe estar ocupada'}, status=400)
        
        # Obtener y validar el destino asignado
        destino_asignado = data.get('destino_asignado', '')
        if not destino_asignado:
            return JsonResponse({'error': 'Debe proporcionar el destino asignado'}, status=400)
        
        # Validar que el destino sea válido
        destinos_validos = [d[0] for d in Posicion.DESTINOS]
        if destino_asignado not in destinos_validos:
            return JsonResponse({'error': 'Destino inválido'}, status=400)
        
        # Marcar el destino asignado y el timestamp (esto detiene el cronómetro)
        posicion.destino_asignado = destino_asignado
        posicion.timestamp_destino_asignado = timezone.now()
        posicion.save()
        
        # Crear evento en el historial
        if posicion.timestamp_ingreso and posicion.nombre_paciente:
            EventoEgreso.objects.create(
                posicion_id=posicion_id,
                paciente=posicion.nombre_paciente,
                destino=destino_asignado,
                timestamp_ingreso=posicion.timestamp_ingreso,
                timestamp_egreso=posicion.timestamp_destino_asignado,
            )
        
        return JsonResponse({
            'success': True,
            'posicion': {
                'id': posicion.id,
                'estado': posicion.estado,
                'nombre_paciente': posicion.nombre_paciente,
                'timestamp_ingreso': posicion.timestamp_ingreso.isoformat() if posicion.timestamp_ingreso else None,
                'destino_solicitado': posicion.destino_solicitado,
                'destino_asignado': posicion.destino_asignado,
                'timestamp_destino_asignado': posicion.timestamp_destino_asignado.isoformat(),
            }
        })
        
    except Posicion.DoesNotExist:
        return JsonResponse({'error': 'Posición no encontrada'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def historial(request):
    """
    Vista del historial de pacientes con estadísticas de tiempos de espera.
    Permite identificar cuellos de botella por destino.
    """
    from django.db.models import Avg, Count, Min, Max
    from datetime import timedelta
    
    # Obtener todos los eventos de egreso (historial completo)
    eventos = EventoEgreso.objects.all().order_by('-timestamp_egreso')
    
    # Calcular estadísticas por destino
    estadisticas_por_destino = {}
    for destino_codigo, destino_nombre in Posicion.DESTINOS:
        eventos_destino = eventos.filter(destino=destino_codigo)
        
        if eventos_destino.exists():
            # Obtener duraciones
            duraciones = [e.duracion.total_seconds() / 60 for e in eventos_destino if e.duracion]
            
            if duraciones:
                estadisticas_por_destino[destino_codigo] = {
                    'nombre': destino_nombre,
                    'total_pacientes': eventos_destino.count(),
                    'tiempo_promedio_minutos': sum(duraciones) / len(duraciones),
                    'tiempo_minimo_minutos': min(duraciones),
                    'tiempo_maximo_minutos': max(duraciones),
                }
    
    # Estadísticas generales
    total_eventos = eventos.count()
    if total_eventos > 0:
        todas_duraciones = [e.duracion.total_seconds() / 60 for e in eventos if e.duracion]
        tiempo_promedio_general = sum(todas_duraciones) / len(todas_duraciones) if todas_duraciones else 0
    else:
        tiempo_promedio_general = 0
    
    # Eventos recientes con duración formateada
    eventos_lista = []
    for evento in eventos[:50]:  # Últimos 50 eventos
        duracion_minutos = int(evento.duracion.total_seconds() / 60) if evento.duracion else 0
        horas = duracion_minutos // 60
        minutos = duracion_minutos % 60
        
        eventos_lista.append({
            'id': evento.id,
            'posicion_id': evento.posicion_id,
            'paciente': evento.paciente,
            'destino': evento.get_destino_display(),
            'destino_codigo': evento.destino,
            'timestamp_ingreso': evento.timestamp_ingreso,
            'timestamp_egreso': evento.timestamp_egreso,
            'duracion_minutos': duracion_minutos,
            'duracion_formateada': f"{horas}h {minutos}m" if horas > 0 else f"{minutos}m",
        })
    
    return render(request, 'guardia/historial.html', {
        'eventos': eventos_lista,
        'estadisticas_por_destino': estadisticas_por_destino,
        'total_eventos': total_eventos,
        'tiempo_promedio_general': tiempo_promedio_general,
    })
