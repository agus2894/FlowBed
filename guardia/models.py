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
    
    # id es string, no autoincremental (ej: "C1", "CONS1", "SR1", "ISO1")
    id = models.CharField(max_length=10, primary_key=True)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='LIBRE')
    timestamp_estado = models.DateTimeField(auto_now=True)
    nombre_paciente = models.CharField(max_length=200, blank=True, null=True)
    
    # Campos para cronómetro y destino
    timestamp_ingreso = models.DateTimeField(null=True, blank=True)  # Cuándo se ocupó
    destino_solicitado = models.CharField(max_length=10, choices=DESTINOS, blank=True, null=True)  # A dónde irá
    
    # Campos para el destino final asignado (detiene el cronómetro)
    destino_asignado = models.CharField(max_length=10, choices=DESTINOS, blank=True, null=True)  # Dónde fue finalmente
    timestamp_destino_asignado = models.DateTimeField(null=True, blank=True)  # Cuándo se asignó el destino
    
    class Meta:
        verbose_name = "Posición"
        verbose_name_plural = "Posiciones"
        ordering = ['id']
    
    def __str__(self):
        return f"{self.id} ({self.get_tipo_display()}) - {self.estado}"


class EventoEgreso(models.Model):
    """
    Registra cuando un paciente egresa de una posición.
    Se crea cuando una posición pasa de OCUPADO a LIMPIEZA.
    """
    DESTINOS = [
        ('PISO', 'Piso'),
        ('UTI', 'UTI'),
        ('UTIM', 'UTIM'),
    ]
    
    posicion_id = models.CharField(max_length=10)
    paciente = models.CharField(max_length=200)
    destino = models.CharField(max_length=10, choices=DESTINOS)
    timestamp_ingreso = models.DateTimeField()
    timestamp_egreso = models.DateTimeField(auto_now_add=True)
    duracion = models.DurationField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Evento de Egreso"
        verbose_name_plural = "Eventos de Egreso"
        ordering = ['-timestamp_egreso']
    
    def save(self, *args, **kwargs):
        """Calcula automáticamente la duración antes de guardar"""
        if self.timestamp_ingreso and self.timestamp_egreso:
            self.duracion = self.timestamp_egreso - self.timestamp_ingreso
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.paciente} - {self.posicion_id} → {self.destino}"
