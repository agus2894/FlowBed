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
        self.assertIsNotNone(self.cama.timestamp_ingreso)

    def test_actualizar_estado_sin_paciente_falla(self):
        payload = {
            'estado': 'OCUPADO',
            'nombre_paciente': '',
            'destino_solicitado': 'PISO'
        }
        response = self.client.post(
            reverse('guardia:actualizar_estado', args=['C1']),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_marcar_destino_asignado_crea_evento(self):
        # Primero ocupar cama
        self.cama.estado = 'OCUPADO'
        self.cama.nombre_paciente = 'Ana Maria'
        self.cama.destino_solicitado = 'UTI'
        self.cama.timestamp_ingreso = timezone.now()
        self.cama.save()

        payload = {'destino_asignado': 'UTI'}
        response = self.client.post(
            reverse('guardia:marcar_destino_asignado', args=['C1']),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

        self.cama.refresh_from_db()
        self.assertEqual(self.cama.destino_asignado, 'UTI')
        self.assertIsNotNone(self.cama.timestamp_destino_asignado)

        # Verificar que se creó el evento de egreso
        evento = EventoEgreso.objects.filter(posicion_id='C1', paciente='Ana Maria').first()
        self.assertIsNotNone(evento)
        self.assertEqual(evento.destino, 'UTI')

    def test_historial_view(self):
        EventoEgreso.objects.create(
            posicion_id='C1',
            paciente='Test Paciente',
            destino='PISO',
            timestamp_ingreso=timezone.now() - timezone.timedelta(minutes=45),
            timestamp_egreso=timezone.now()
        )
        response = self.client.get(reverse('guardia:historial'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Paciente')
        self.assertContains(response, 'chart-data-payload')
