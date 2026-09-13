from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
import json
from .models import Posicion, EventoEgreso


class GuardiaTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.cama = Posicion.objects.create(
            id='C1',
            tipo='cama',
            estado='LIBRE'
        )
        self.shock = Posicion.objects.create(
            id='SR1',
            tipo='shock',
            estado='LIBRE'
        )

    def test_dashboard_view(self):
        response = self.client.get(reverse('guardia:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'FlowBed')
        self.assertContains(response, 'C1')

    def test_obtener_posiciones_api(self):
        response = self.client.get(reverse('guardia:obtener_posiciones'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('posiciones', data)
        self.assertEqual(len(data['posiciones']), 2)

    def test_stream_posiciones_headers(self):
        response = self.client.get(reverse('guardia:stream_posiciones'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/event-stream')

    def test_actualizar_estado_a_ocupado(self):
        payload = {
            'estado': 'OCUPADO',
            'nombre_paciente': 'Carlos Gardel',
            'destino_solicitado': 'PISO'
        }
        response = self.client.post(
            reverse('guardia:actualizar_estado', args=['C1']),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

        self.cama.refresh_from_db()
        self.assertEqual(self.cama.estado, 'OCUPADO')
        self.assertEqual(self.cama.nombre_paciente, 'Carlos Gardel')
        self.assertEqual(self.cama.destino_solicitado, 'PISO')
        self.assertEqual(self.cama.etapa_circuito, 'SOLICITADA')
        self.assertIsNotNone(self.cama.timestamp_ingreso)

    def test_actualizar_estado_sin_destino_no_falla(self):
        """El destino es opcional al ingresar: el paciente puede quedar en Atención."""
        payload = {
            'estado': 'OCUPADO',
            'nombre_paciente': 'Mario Gomez',
        }
        response = self.client.post(
            reverse('guardia:actualizar_estado', args=['C1']),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.cama.refresh_from_db()
        self.assertEqual(self.cama.etapa_circuito, 'ATENCION')

    def test_actualizar_estado_sin_paciente_falla(self):
        payload = {
            'estado': 'OCUPADO',
            'nombre_paciente': '',
        }
        response = self.client.post(
            reverse('guardia:actualizar_estado', args=['C1']),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_circuito_asistencial_completo(self):
        """
        Prueba el ciclo de vida completo:
        1. Ingreso de Paciente -> OCUPADO, ATENCION
        2. Solicitud de Cama -> SOLICITADA
        3. Aceptar / Asignar Cama -> ASIGNADA
        4. Confirmar Traslado -> Cama a LIMPIEZA, EventoEgreso creado
        5. Completar Limpieza -> Cama a LIBRE
        """
        # Paso 1: Ingreso de Paciente
        payload_ingreso = {
            'estado': 'OCUPADO',
            'nombre_paciente': 'Mario Gomez'
        }
        res1 = self.client.post(
            reverse('guardia:actualizar_estado', args=['C1']),
            data=json.dumps(payload_ingreso),
            content_type='application/json'
        )
        self.assertEqual(res1.status_code, 200)
        self.cama.refresh_from_db()
        self.assertEqual(self.cama.estado, 'OCUPADO')
        self.assertEqual(self.cama.nombre_paciente, 'Mario Gomez')
        self.assertEqual(self.cama.etapa_circuito, 'ATENCION')
        self.assertIsNotNone(self.cama.timestamp_ingreso)

        # Paso 2: Solicitar Cama
        payload_solicitud = {'destino_solicitado': 'UTI'}
        res2 = self.client.post(
            reverse('guardia:solicitar_cama', args=['C1']),
            data=json.dumps(payload_solicitud),
            content_type='application/json'
        )
        self.assertEqual(res2.status_code, 200)
        self.cama.refresh_from_db()
        self.assertEqual(self.cama.etapa_circuito, 'SOLICITADA')
        self.assertEqual(self.cama.destino_solicitado, 'UTI')
        self.assertIsNotNone(self.cama.timestamp_solicitud)

        # Paso 3: Aceptar / Asignar Cama
        payload_asignacion = {
            'destino_asignado': 'UTI',
            'cama_asignada_detalle': 'Cama 4 - Sector A'
        }
        res3 = self.client.post(
            reverse('guardia:aceptar_asignar_cama', args=['C1']),
            data=json.dumps(payload_asignacion),
            content_type='application/json'
        )
        self.assertEqual(res3.status_code, 200)
        self.cama.refresh_from_db()
        self.assertEqual(self.cama.etapa_circuito, 'ASIGNADA')
        self.assertEqual(self.cama.destino_asignado, 'UTI')
        self.assertEqual(self.cama.cama_asignada_detalle, 'Cama 4 - Sector A')
        self.assertIsNotNone(self.cama.timestamp_destino_asignado)
        # La cama de guardia sigue OCUPADA: el paciente todavía no fue trasladado
        self.assertEqual(self.cama.estado, 'OCUPADO')
        self.assertEqual(EventoEgreso.objects.filter(posicion_id='C1').count(), 0)

        # Paso 4: Confirmar Traslado del Paciente (pasa a LIMPIEZA)
        payload_traslado = {'siguiente_estado': 'LIMPIEZA'}
        res4 = self.client.post(
            reverse('guardia:trasladar_egresar_paciente', args=['C1']),
            data=json.dumps(payload_traslado),
            content_type='application/json'
        )
        self.assertEqual(res4.status_code, 200)
        self.cama.refresh_from_db()
        self.assertEqual(self.cama.estado, 'LIMPIEZA')
        self.assertIsNone(self.cama.nombre_paciente)
        self.assertEqual(self.cama.etapa_circuito, 'ATENCION')

        # Verificar creación única del evento en Historial
        eventos = EventoEgreso.objects.filter(posicion_id='C1', paciente='Mario Gomez')
        self.assertEqual(eventos.count(), 1)
        evento = eventos.first()
        self.assertEqual(evento.destino, 'UTI')
        self.assertEqual(evento.cama_asignada_detalle, 'Cama 4 - Sector A')
        self.assertIsNotNone(evento.duracion_espera_cama)
        self.assertIsNotNone(evento.duracion_total_guardia)

        # Paso 5: Completar Limpieza -> LIBRE
        res5 = self.client.post(
            reverse('guardia:completar_limpieza', args=['C1']),
            content_type='application/json'
        )
        self.assertEqual(res5.status_code, 200)
        self.cama.refresh_from_db()
        self.assertEqual(self.cama.estado, 'LIBRE')

    def test_historial_view(self):
        EventoEgreso.objects.create(
            posicion_id='C1',
            paciente='Test Paciente',
            destino='PISO',
            cama_asignada_detalle='Cama 101',
            timestamp_ingreso=timezone.now() - timezone.timedelta(minutes=60),
            timestamp_solicitud=timezone.now() - timezone.timedelta(minutes=50),
            timestamp_asignacion=timezone.now() - timezone.timedelta(minutes=10),
            timestamp_egreso=timezone.now()
        )
        response = self.client.get(reverse('guardia:historial'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Paciente')
        self.assertContains(response, 'Cama 101')
        self.assertContains(response, 'chart-data-payload')

