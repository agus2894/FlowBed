from django.db import models
from django.utils import timezone


class Posicion(models.Model):
    """
    Representa una posición asistencial en la guardia hospitalaria.
    Puede ser: cama, consultorio, shock room o aislamiento.
    """
    TIPOS = [
        ('cama', 'Cama'),
        ('consultorio', 'Consultorio'),
        ('shock', 'Shock Room'),
        ('aislamiento', 'Aislamiento'),
    ]
    
    ESTADOS = [
        ('LIBRE', 'Libre'),
        ('OCUPADO', 'Ocupado'),
        ('LIMPIEZA', 'En Limpieza'),
        ('RESERVADO', 'Reservado'),
        ('FUERA_SERVICIO', 'Fuera de Servicio'),
    ]
    
    DESTINOS = [
        ('PISO', 'Piso'),
        ('UTI', 'UTI'),
        ('UTIM', 'UTIM'),
    ]

    ETAPAS = [
        ('ATENCION', 'En Atención'),
        ('SOLICITADA', 'Cama Solicitada'),
        ('ASIGNADA', 'Cama Asignada'),
    ]
    
    # id es string, no autoincremental (ej: "C1", "CONS1", "SR1", "ISO1")
    id = models.CharField(max_length=10, primary_key=True)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='LIBRE')
    timestamp_estado = models.DateTimeField(auto_now=True)
    
    # Datos del paciente en guardia
    nombre_paciente = models.CharField(max_length=200, blank=True, null=True)
    timestamp_ingreso = models.DateTimeField(null=True, blank=True)  # Cuándo ingresó a la guardia

    # Circuito de asignación de cama
    etapa_circuito = models.CharField(max_length=20, choices=ETAPAS, default='ATENCION')

    # Solicitud de cama
    destino_solicitado = models.CharField(max_length=10, choices=DESTINOS, blank=True, null=True)
    timestamp_solicitud = models.DateTimeField(null=True, blank=True)  # Cuándo se solicitó cama a internación
    
    # Aceptación y Asignación de cama
    destino_asignado = models.CharField(max_length=10, choices=DESTINOS, blank=True, null=True)
    cama_asignada_detalle = models.CharField(max_length=100, blank=True, null=True)  # ej: "Piso 3 - Cama 304"
    timestamp_destino_asignado = models.DateTimeField(null=True, blank=True)  # Cuándo se aceptó la cama
    
    class Meta:
        verbose_name = "Posición"
        verbose_name_plural = "Posiciones"
        ordering = ['id']
    
    def __str__(self):
        return f"{self.id} ({self.get_tipo_display()}) - {self.estado}"


class EventoEgreso(models.Model):
    """
    Registra cuando un paciente egresa / es trasladado de una posición de guardia.
    """
    DESTINOS = [
        ('PISO', 'Piso'),
        ('UTI', 'UTI'),
        ('UTIM', 'UTIM'),
    ]
    
    posicion_id = models.CharField(max_length=10)
    paciente = models.CharField(max_length=200)
    destino = models.CharField(max_length=10, choices=DESTINOS)
    cama_asignada_detalle = models.CharField(max_length=100, blank=True, null=True)
    
    timestamp_ingreso = models.DateTimeField()
    timestamp_solicitud = models.DateTimeField(null=True, blank=True)
    timestamp_asignacion = models.DateTimeField(null=True, blank=True)
    timestamp_egreso = models.DateTimeField(default=timezone.now)
    
    # Métricas calculadas
    duracion_espera_cama = models.DurationField(null=True, blank=True)  # timestamp_asignacion - timestamp_solicitud
    duracion = models.DurationField(null=True, blank=True)  # compatibilidad
    duracion_total_guardia = models.DurationField(null=True, blank=True)  # timestamp_egreso - timestamp_ingreso
    
    class Meta:
        verbose_name = "Evento de Egreso"
        verbose_name_plural = "Eventos de Egreso"
        ordering = ['-timestamp_egreso']
    
    def save(self, *args, **kwargs):
        """Calcula automáticamente las duraciones antes de guardar"""
        if self.timestamp_solicitud and self.timestamp_asignacion:
            self.duracion_espera_cama = self.timestamp_asignacion - self.timestamp_solicitud
            self.duracion = self.duracion_espera_cama

        if self.timestamp_ingreso and self.timestamp_egreso:
            self.duracion_total_guardia = self.timestamp_egreso - self.timestamp_ingreso
            if not self.duracion:
                self.duracion = self.duracion_total_guardia

        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.paciente} - {self.posicion_id} → {self.destino}"

