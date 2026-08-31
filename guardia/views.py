"""
Vistas para la gestión de la guardia hospitalaria.
"""
from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json
import time

from .models import Posicion, EventoEgreso


def _serializar_posiciones():
    """Helper para serializar todas las posiciones a lista de diccionarios"""
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
    return datos


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
    return JsonResponse({'posiciones': _serializar_posiciones()})


def stream_posiciones(request):
    """
    API SSE: Transmite eventos en tiempo real mediante Server-Sent Events.
    Notifica al instante a todos los navegadores conectados cuando cambia el estado de una posición.
    """
    def event_stream():
        # Envía el estado inicial
        posiciones_iniciales = _serializar_posiciones()
        ultimo_hash = hash(json.dumps(posiciones_iniciales, sort_keys=True))
        yield f"event: init\ndata: {json.dumps({'posiciones': posiciones_iniciales})}\n\n"

        while True:
            time.sleep(1)
            posiciones_actuales = _serializar_posiciones()
            hash_actual = hash(json.dumps(posiciones_actuales, sort_keys=True))

            if hash_actual != ultimo_hash:
                ultimo_hash = hash_actual
                yield f"event: update\ndata: {json.dumps({'posiciones': posiciones_actuales})}\n\n"
            elif int(time.time()) % 15 == 0:
                # Keep-alive heartbeat
                yield ": ping\n\n"

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


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
                    EventoEgreso.objects.create(
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
    Permite identificar cuellos de botella por destino y genera datos para Chart.js.
    """
    eventos = EventoEgreso.objects.all().order_by('-timestamp_egreso')
    
    # Estadísticas por destino y datos para gráficos
    estadisticas_por_destino = {}
    chart_labels = []
    chart_avg_data = []
    chart_counts_data = []
    colores_map = {
        'PISO': '#3498db',
        'UTI': '#e74c3c',
        'UTIM': '#f39c12',
    }
    chart_colors = []
    
    for destino_codigo, destino_nombre in Posicion.DESTINOS:
        eventos_destino = eventos.filter(destino=destino_codigo)
        total_d = eventos_destino.count()
        
        if total_d > 0:
            duraciones = [e.duracion.total_seconds() / 60 for e in eventos_destino if e.duracion]
            if duraciones:
                promedio = round(sum(duraciones) / len(duraciones), 1)
                minimo = round(min(duraciones), 1)
                maximo = round(max(duraciones), 1)
                
                estadisticas_por_destino[destino_codigo] = {
                    'nombre': destino_nombre,
                    'total_pacientes': total_d,
                    'tiempo_promedio_minutos': promedio,
                    'tiempo_minimo_minutos': minimo,
                    'tiempo_maximo_minutos': maximo,
                }
                
                chart_labels.append(destino_nombre)
                chart_avg_data.append(promedio)
                chart_counts_data.append(total_d)
                chart_colors.append(colores_map.get(destino_codigo, '#3498db'))
    
    # Estadísticas generales
    total_eventos = eventos.count()
    if total_eventos > 0:
        todas_duraciones = [e.duracion.total_seconds() / 60 for e in eventos if e.duracion]
        tiempo_promedio_general = round(sum(todas_duraciones) / len(todas_duraciones), 1) if todas_duraciones else 0
    else:
        tiempo_promedio_general = 0
    
    # Eventos recientes (últimos 100)
    eventos_lista = []
    for evento in eventos[:100]:
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
    
    chart_data_json = json.dumps({
        'labels': chart_labels,
        'avg_times': chart_avg_data,
        'counts': chart_counts_data,
        'colors': chart_colors,
    })
    
    return render(request, 'guardia/historial.html', {
        'eventos': eventos_lista,
        'estadisticas_por_destino': estadisticas_por_destino,
        'total_eventos': total_eventos,
        'tiempo_promedio_general': tiempo_promedio_general,
        'chart_data_json': chart_data_json,
    })

